"""
Proxies tile requests to a TiTiler instance for serving Cloud-Optimized
GeoTIFFs (COGs) to the frontend map viewer.
"""
from fastapi import APIRouter, HTTPException
import os

router = APIRouter(prefix="/tiles", tags=["tiles"])

TITILER_URL = os.environ.get("TITILER_URL", "http://titiler:8000")


@router.get("/{z}/{x}/{y}.png")
def get_tile(z: int, x: int, y: int, url: str):
    """
    TODO: proxy to TiTiler's /cog/tiles/{z}/{x}/{y}.png?url=<cog_url> endpoint.
    Stubbed until TiTiler service is added to docker-compose.
    """
    raise HTTPException(status_code=501, detail="TiTiler proxy not yet implemented")
