from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict
import uuid
import os

app = FastAPI(title="satelite-image-scan API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory job store (placeholder — swap for a real DB later)
jobs: Dict[str, dict] = {}


class TileProcessRequest(BaseModel):
    tile_filename: str


@app.get("/status")
def get_status(job_id: str | None = None):
    """
    Overall API health check, or status of a specific job if job_id is given.
    """
    if job_id is None:
        return {"status": "ok"}

    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Accepts an image upload (e.g. a full swath or a single tile) and
    stores it on disk. Returns a job_id you can poll via /status.
    """
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

    return jobs[job_id]


@app.post("/process-tile")
def process_tile(request: TileProcessRequest):
    """
    Placeholder endpoint for triggering processing/detection on a single tile.
    Replace the body with real model inference later.
    """
    tile_path = os.path.join(UPLOAD_DIR, request.tile_filename)
    if not os.path.exists(tile_path):
        raise HTTPException(status_code=404, detail="Tile not found")

    # TODO: replace with real detection/processing logic
    result = {
        "tile_filename": request.tile_filename,
        "detections": [],
        "status": "processed (placeholder)",
    }

    return result
