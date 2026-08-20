# ISRO SR Hackathon — Team Eclipse

Super-resolution satellite imagery pipeline.

## Structure

- `ml_engine/` — SR model, training, inference (Aryaman)
- `backend/` — FastAPI + Celery/Redis async processing (Johith)
- `frontend/` — Next.js dashboard (Bassil)

## Local dev (all services)

    docker-compose up --build

Backend API: http://localhost:8000/docs
