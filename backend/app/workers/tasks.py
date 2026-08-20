"""
backend/queue/tasks.py

Celery task definitions for the complete pipeline orchestration:
Tile Cutting -> Cached AI Processing -> Seamless Stitching -> COG Conversion.
"""

import os
import glob
import shutil
from typing import Dict, Any, List
from celery import chord

from queue.celery_app import celery_app
from queue.job_state import (
    generate_tile_hash,
    get_cached_tile,
    set_cached_tile,
    set_job_progress
)
from tiler.tile_cutter import slice_geotiff
from postprocess.stitcher import stitch_processed_tiles
from postprocess.cog_writer import convert_to_cog


@celery_app.task(name="tasks.process_tile_task")
def process_tile_task(
    tile_file: str, 
    bounds: List[float], 
    pipeline_params: Dict[str, Any], 
    output_dir: str
) -> str:
    """
    Individual task processing a single image tile.
    Checks Redis cache first before calling AI Engine.
    """
    tile_hash = generate_tile_hash(bounds, pipeline_params)
    tile_name = os.path.basename(tile_file)
    target_output_path = os.path.join(output_dir, tile_name)

    os.makedirs(output_dir, exist_ok=True)

    # 1. CACHE HIT: Copy cached processed tile
    cached_result = get_cached_tile(tile_hash)
    if cached_result and os.path.exists(cached_result.get("output_path", "")):
        shutil.copy(cached_result["output_path"], target_output_path)
        return target_output_path

    # 2. CACHE MISS: Fall back to AI engine processing worker
    # Note: Imports dynamically to handle monorepo worker dependencies
    try:
        from ai_engine.main import run_ai_pipeline
        processed_path = run_ai_pipeline(tile_file, pipeline_params, target_output_path)
    except ImportError:
        # Fallback placeholder if AI engine module isn't loaded on worker node
        shutil.copy(tile_file, target_output_path)
        processed_path = target_output_path

    # 3. Cache processed result in Redis
    set_cached_tile(tile_hash, processed_path)

    return processed_path


@celery_app.task(name="tasks.finalize_job_task")
def finalize_job_task(
    tile_results: List[str], 
    job_id: str, 
    processed_tile_dir: str, 
    final_output_dir: str,
    overlap_px: int = 32
) -> Dict[str, Any]:
    """
    Callback task executed after ALL parallel tile processing tasks complete.
    Stitches tiles seamlessly and exports final Cloud-Optimized GeoTIFF.
    """
    os.makedirs(final_output_dir, exist_ok=True)
    
    stitched_tif_path = os.path.join(final_output_dir, f"{job_id}_stitched.tif")
    cog_output_path = os.path.join(final_output_dir, f"{job_id}_cog.tif")

    # 1. Update job state to POST_PROCESSING
    set_job_progress(job_id, total_tiles=len(tile_results), completed_tiles=len(tile_results), status="STITCHING")

    # 2. Stitch processed tiles seamlessly
    stitch_processed_tiles(
        tile_dir=processed_tile_dir,
        output_geotiff_path=stitched_tif_path,
        overlap_px=overlap_px
    )

    # 3. Convert stitched output to Cloud-Optimized GeoTIFF
    convert_to_cog(
        input_path=stitched_tif_path,
        output_path=cog_output_path
    )

    # 4. Mark job as COMPLETED
    set_job_progress(job_id, total_tiles=len(tile_results), completed_tiles=len(tile_results), status="COMPLETED")

    return {
        "job_id": job_id,
        "status": "COMPLETED",
        "cog_path": cog_output_path
    }


@celery_app.task(name="tasks.orchestrate_image_pipeline")
def orchestrate_image_pipeline(
    job_id: str, 
    input_geotiff_path: str, 
    pipeline_params: Dict[str, Any],
    work_dir: str = "/tmp/jobs"
) -> str:
    """
    Main orchestration entrypoint triggered by FastAPI POST /upload.
    """
    job_dir = os.path.join(work_dir, job_id)
    raw_tiles_dir = os.path.join(job_dir, "raw_tiles")
    processed_tiles_dir = os.path.join(job_dir, "processed_tiles")
    output_dir = os.path.join(job_dir, "output")

    # 1. Step 1: Slice raw GeoTIFF into overlapping tiles
    set_job_progress(job_id, total_tiles=0, completed_tiles=0, status="TILING")
    tile_manifest = slice_geotiff(
        input_path=input_geotiff_path,
        output_dir=raw_tiles_dir,
        tile_size=512,
        overlap_px=32
    )

    total_tiles = len(tile_manifest)
    set_job_progress(job_id, total_tiles=total_tiles, completed_tiles=0, status="PROCESSING")

    # 2. Step 2: Build parallel task chord
    header = [
        process_tile_task.s(
            tile_file=item["file_path"],
            bounds=item["bounds"],
            pipeline_params=pipeline_params,
            output_dir=processed_tiles_dir
        )
        for item in tile_manifest
    ]

    callback = finalize_job_task.s(
        job_id=job_id,
        processed_tile_dir=processed_tiles_dir,
        final_output_dir=output_dir,
        overlap_px=32
    )

    # Dispatch chord to Celery workers
    chord(header)(callback)
    return job_id