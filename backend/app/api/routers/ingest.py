"""
backend/app/api/routers/ingest.py

Endpoint for uploading satellite GeoTIFF files, validating format/CRS,
and dispatching tasks to Celery workers.
"""

import os
import uuid
import shutil
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from app.services.metadata_extraction.extractor import validate_and_extract_metadata
from app.workers.tasks import orchestrate_image_pipeline

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_geotiff(
    file: UploadFile = File(...),
    dehaze: bool = Form(True),
    super_resolution: bool = Form(False),
    inpaint: bool = Form(False)
) -> Dict[str, Any]:
    """
    Ingests GeoTIFF files, extracts metadata/CRS routing hints, and queues Celery jobs.
    """
    if not file.filename.lower().endswith(('.tif', '.tiff', '.geotiff')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only GeoTIFF files (.tif, .tiff) are accepted."
        )

    job_id = str(uuid.uuid4())
    job_upload_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)

    input_file_path = os.path.join(job_upload_dir, file.filename)

    try:
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save upload payload: {str(e)}"
        )

    validation = validate_and_extract_metadata(input_file_path)
    if not validation["is_valid"]:
        shutil.rmtree(job_upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GeoTIFF Validation Error: {validation['error']}"
        )

    pipeline_params = {
        "dehaze": dehaze,
        "super_resolution": super_resolution,
        "inpaint": inpaint
    }

    orchestrate_image_pipeline.delay(
        job_id=job_id,
        input_geotiff_path=input_file_path,
        pipeline_params=pipeline_params
    )

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "message": "File ingested and queued successfully.",
        "metadata": validation.get("metadata", {})
    }
