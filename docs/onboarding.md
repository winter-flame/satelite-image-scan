# Onboarding

## Setup

1. Clone the repo and `cd` into it.
2. Copy `.env.example` to `.env` and fill in Redis / S3-GCS credentials (ask Johith if you don't have these yet).
3. From repo root, run: `docker-compose -f infra/docker-compose.yml up`

   This brings up Redis, the FastAPI backend, and the Celery worker. (Frontend and ai-engine services will be added to this compose file as those directories come online.)

## Where things live

- `backend/app/` — FastAPI routers, services, Celery workers, models
- `infra/` — docker-compose, TiTiler config, k8s manifests (if needed)
- `shared/schemas/` — cross-service contracts (see `docs/schemas/README.md`)
- `frontend/` — Next.js WebGIS app (Bassil)
- `ai-engine/` — orchestrator + correction models (Aryaman + team)

## Local backend dev (without full docker-compose)

Run these commands in order:

    cd backend
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Visit `http://localhost:8000/docs` for interactive API docs.
