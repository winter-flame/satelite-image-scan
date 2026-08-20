# TiTiler service config

TiTiler serves Cloud-Optimized GeoTIFFs (COGs) as XYZ tiles to the frontend map viewer.

TODO:
- Add TiTiler as a service in ../docker-compose.yml (image: ghcr.io/developmentseed/titiler)
- Point backend/app/api/routers/tiles.py's TITILER_URL env var at it
- Configure allowed COG source buckets (S3/GCS) once storage is wired up
