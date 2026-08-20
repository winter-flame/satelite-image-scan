"""
Job creation, status polling, and live status via WebSocket.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from celery.result import AsyncResult
import os
import asyncio

from app.workers.celery_app import celery_app
from app.workers.tasks import process_tile_task
from app.api.routers.ingest import jobs, UPLOAD_DIR

router = APIRouter(prefix="/jobs", tags=["jobs"])


class TileProcessRequest(BaseModel):
    tile_filename: str


@router.post("/process-tile")
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


@router.get("/status")
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


@router.websocket("/ws/{task_id}")
async def job_status_ws(websocket: WebSocket, task_id: str):
    """
    Pushes task status updates until the task completes or the client disconnects.
    """
    await websocket.accept()
    try:
        while True:
            result = AsyncResult(task_id, app=celery_app)
            await websocket.send_json({"task_id": task_id, "state": result.state})
            if result.ready():
                await websocket.send_json({
                    "task_id": task_id,
                    "state": result.state,
                    "result": result.result,
                })
                break
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
