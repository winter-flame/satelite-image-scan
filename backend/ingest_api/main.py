"""
backend/ingest_api/main.py

Main FastAPI application for Member 2 Ingest Service.
Handles file uploads, validation, pipeline triggering, and job status polling.
"""

import os
import uuid
import shutil
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware

from ingest_api.validators import validate_geotiff
from ingest_api.models import JobResponse, JobStatusResponse
from queue.tasks import orchestrate_image_pipeline
from queue.job_state import redis_client

app = FastAPI(
    title="Satellite Image Enhancement - Ingest API",
    version="1.0.0",
    description="Backend service for GeoTIFF upload ingestion, orchestration, and state tracking."
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint to verify Redis and API availability."""
    try:
        redis_ping = redis_client.ping()
        redis_status = "healthy" if redis_ping else "unhealthy"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "online",
        "redis": redis_status
    }


@app.post("/upload", response_model=JobResponse, status_code=202)
async def upload_geotiff(
    file: UploadFile = File(...),
    dehaze: bool = Form(True),
    super_resolution: bool = Form(False),
    inpaint: bool = Form(False)
) -> JobResponse:
    """
    Ingests raw satellite GeoTIFF files, validates headers, and triggers asynchronous task pipeline.
    """
    if not file.filename.lower().endswith(('.tif', '.tiff', '.geotiff')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only GeoTIFF files (.tif, .tiff) are accepted.")

    job_id = str(uuid.uuid4())
    job_upload_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)

    input_file_path = os.path.join(job_upload_dir, file.filename)

    # Save uploaded file payload to disk
    try:
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Validate GeoTIFF format, CRS, band configuration
    validation_result = validate_geotiff(input_file_path)
    if not validation_result["is_valid"]:
        shutil.rmtree(job_upload_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"GeoTIFF Validation Failed: {validation_result['error']}")

    pipeline_params = {
        "dehaze": dehaze,
        "super_resolution": super_resolution,
        "inpaint": inpaint
    }

    # Dispatch asynchronous Celery pipeline
    orchestrate_image_pipeline.delay(
        job_id=job_id,
        input_geotiff_path=input_file_path,
        pipeline_params=pipeline_params
    )

    return JobResponse(
        job_id=job_id,
        status="QUEUED",
        message="GeoTIFF uploaded and processing job queued successfully.",
        metadata=validation_result.get("metadata", {})
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Polls current job progress status and completion counters from Redis.
    """
    job_key = f"job:{job_id}"
    job_data = redis_client.hgetall(job_key)

    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found.")

    status = job_data.get("status", "UNKNOWN")
    total_tiles = int(job_data.get("total_tiles", 0))
    completed_tiles = int(job_data.get("completed_tiles", 0))

    progress_percentage = (completed_tiles / total_tiles * 100.0) if total_tiles > 0 else 0.0

    return JobStatusResponse(
        job_id=job_id,
        status=status,
        total_tiles=total_tiles,
        completed_tiles=completed_tiles,
        progress=round(progress_percentage, 2)
    )