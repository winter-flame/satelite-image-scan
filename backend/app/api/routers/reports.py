"""
Read-only endpoints for scientific report generation/retrieval.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{job_id}")
def get_report(job_id: str):
    # TODO: assemble report from provenance + benchmark_store data
    raise HTTPException(status_code=501, detail="Reports not yet implemented")
