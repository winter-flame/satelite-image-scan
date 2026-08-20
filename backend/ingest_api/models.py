"""Pydantic request/response schemas."""
from pydantic import BaseModel


class JobResponse(BaseModel):
    job_id: str
    filename: str
    status: str
    size_bytes: int
