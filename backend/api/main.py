from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict
from celery.result import AsyncResult
import uuid
import os

from core.celery_app import celery_app
from core.worker import process_tile_task

app = FastAPI(title="satelite-image-scan API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

jobs: Dict[str, dict] = {}


class TileProcessRequest(BaseModel):
    tile_filename: str


@app.get("/status")
def get_status(job_id: str | None = None, task_id: str | None = None):
    if task_id:
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "state": result.state,
            "result": result.result if result.ready() else None,
        }

    if job_id:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    return {"status": "ok"}


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
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
    tile_path = os.path.join(UPLOAD_DIR, request.tile_filename)
    if not os.path.exists(tile_path):
        raise HTTPException(status_code=404, detail="Tile not found")

    task = process_tile_task.delay(request.tile_filename)

    return {
        "tile_filename": request.tile_filename,
        "task_id": task.id,
        "status": "queued",
    }
