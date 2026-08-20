import os
import time
from core.celery_app import celery_app

UPLOAD_DIR = "uploads"


@celery_app.task(bind=True)
def process_tile_task(self, tile_filename: str):
    tile_path = os.path.join(UPLOAD_DIR, tile_filename)

    if not os.path.exists(tile_path):
        return {"tile_filename": tile_filename, "status": "error", "error": "Tile not found"}

    # TODO: replace with real processing (model inference, etc.)
    time.sleep(5)

    return {
        "tile_filename": tile_filename,
        "detections": [],
        "status": "processed (placeholder)",
    }
