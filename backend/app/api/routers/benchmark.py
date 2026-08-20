"""
Read-only endpoints for benchmark scores (baseline vs SR model comparisons).
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


@router.get("/{job_id}")
def get_benchmark(job_id: str):
    # TODO: read from app.services.benchmark_store
    raise HTTPException(status_code=501, detail="Benchmark store not yet implemented")
