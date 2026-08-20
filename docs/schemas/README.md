# Shared Schema Contracts

These describe the four cross-service handoffs in the pipeline. Each schema
lives in `shared/schemas/` as JSON Schema; this file explains them in plain
language. A change to any of these is a PR against `shared/`, reviewed by
both sides of that handoff.

## job_payload.schema.json
**Backend → AI Orchestrator**
Metadata that rides along with each tile job — which pipeline to route to
(from metadata extraction), tile bounds, and routing confidence.

## worker_score.schema.json
**AI Orchestrator ↔ AI Correction Workers**
Common score format used by fidelity gates and the decision engine: NIQE,
BRISQUE, edge SSIM, spectral/radiometric/geometric fidelity, and the
accept/review/reject decision.

## confidence_map.schema.json
**AI Correction Workers → Backend**
Per-pixel "recovered vs. invented" confidence data for a tile. Must survive
the stitching process intact — this is what powers the frontend's
confidence overlay layer.

## scientific_report.schema.json
**AI Validation/Benchmark → Frontend**
Benchmark comparison scores (bicubic/lanczos/ESRGAN vs. system) and
downstream detection deltas (crater/terrain/hazard F1 before vs. after).
