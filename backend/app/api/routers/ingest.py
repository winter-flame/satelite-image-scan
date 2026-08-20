"""
GeoTIFF/PDS4 upload and validation.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import uuid
import os

router = APIRouter(prefix="/ingest", tags=["ingest"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# TODO: move to a real DB-backed store (see app/models, app/db)
jobs: Dict[str, dict] = {}

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".img", ".xml"}  # .img/.xml for PDS4 label+data pairs


def _validate_extension(filename: str) -> None:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    _validate_extension(file.filename)

    job_id = str(uuid.uuid4())
    dest_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")

    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    jobs[job_id] = {
        "job_id": job_id,
        "filename": file.filename,
        "path": dest_path,
        "size_bytes": len(contents),
        "status": "uploaded",
    }

    # TODO: enqueue metadata_extraction service here (sensor, sun elevation, bands)

    return jobs[job_id]
