from fastapi import APIRouter, HTTPException
from app.queue.job_state import redis_client if hasattr(app, 'queue') else None

router = APIRouter()

@router.get("/{job_id}")
def get_job_status(job_id: str):
    return {"job_id": job_id, "status": "PROCESSING"}
