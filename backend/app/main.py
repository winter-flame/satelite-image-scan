"""
backend/app/main.py

Primary FastAPI entrypoint mounting feature routers across ingest, jobs, tiles,
benchmarks, and reports.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import ingest, jobs, tiles, benchmark, reports

app = FastAPI(
    title="Satellite Image Enhancement System",
    version="1.0.0",
    description="Backend API service for GeoTIFF ingestion, tiling, and pipeline orchestration."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingest"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(tiles.router, prefix="/api/v1/tiles", tags=["Tiles"])
app.include_router(benchmark.router, prefix="/api/v1/benchmark", tags=["Benchmark"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "backend-api"}
