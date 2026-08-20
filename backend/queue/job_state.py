"""
backend/queue/job_state.py

Manages job progress states and implements tile-level caching via Redis.
"""

import hashlib
import os
import json
from typing import Optional, Dict, Any
import redis

# Connect to Redis using environment variable or local default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Cache TTL: Default to 7 days (in seconds)
TILE_CACHE_TTL = int(os.getenv("TILE_CACHE_TTL", 604800))


def generate_tile_hash(bounds: Tuple[float, float, float, float], pipeline_params: Dict[str, Any]) -> str:
    """
    Generates a unique SHA-256 hash based on bounding box coordinates 
    and processing parameters (dehaze, inpaint, super-res flags).
    """
    payload = {
        "bounds": [round(b, 6) for b in bounds],  # Round coordinates to avoid float precision mismatch
        "params": pipeline_params
    }
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def get_cached_tile(tile_hash: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves cached tile metadata and output file path from Redis if present.
    """
    cache_key = f"tile_cache:{tile_hash}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        print(f"[Redis Cache HIT] Returning cached result for hash: {tile_hash[:8]}")
        return json.loads(cached_data)
    
    return None


def set_cached_tile(tile_hash: str, output_path: str, metadata: Dict[str, Any] = None) -> None:
    """
    Caches processed tile location and metadata in Redis with an expiration TTL.
    """
    cache_key = f"tile_cache:{tile_hash}"
    payload = {
        "output_path": output_path,
        "metadata": metadata or {}
    }
    redis_client.setex(cache_key, TILE_CACHE_TTL, json.dumps(payload))
    print(f"[Redis Cache SET] Stored tile result for hash: {tile_hash[:8]}")


def set_job_progress(job_id: str, total_tiles: int, completed_tiles: int, status: str = "PROCESSING") -> None:
    """
    Updates the overall job state and progress counters for API polling/WebSockets.
    """
    redis_client.hset(f"job:{job_id}", mapping={
        "status": status,
        "total_tiles": total_tiles,
        "completed_tiles": completed_tiles
    })