from fastapi import FastAPI

from app.api.routers import ingest, jobs, tiles, benchmark, reports

app = FastAPI(title="satelite-image-scan Backend")

app.include_router(ingest.router)
app.include_router(jobs.router)
app.include_router(tiles.router)
app.include_router(benchmark.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}
