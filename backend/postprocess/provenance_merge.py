"""
backend/postprocess/provenance_merge.py

Aggregates per-tile model execution metadata, confidence scores, and pipeline parameters
into a unified job-level provenance ledger for auditing and lineage tracking.
"""

import os
import json
import time
from typing import List, Dict, Any


def merge_tile_provenance(
    job_id: str,
    tile_manifest: List[Dict[str, Any]],
    pipeline_params: Dict[str, Any],
    output_path: str
) -> str:
    """
    Merges tile-level processing records into a single provenance JSON ledger.

    Args:
        job_id (str): Unique job identifier.
        tile_manifest (List[Dict[str, Any]]): List of tile metadata dictionaries.
        pipeline_params (Dict[str, Any]): Pipeline parameters used for processing.
        output_path (str): Destination path for the aggregated JSON file.

    Returns:
        str: Path to the written provenance JSON file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    total_tiles = len(tile_manifest)
    cached_count = sum(1 for tile in tile_manifest if tile.get("from_cache", False))

    provenance_record = {
        "job_id": job_id,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pipeline_parameters": pipeline_params,
        "summary": {
            "total_tiles": total_tiles,
            "processed_tiles": total_tiles - cached_count,
            "cached_tiles": cached_count,
            "cache_hit_ratio": round(cached_count / total_tiles, 4) if total_tiles > 0 else 0.0
        },
        "tile_records": tile_manifest
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(provenance_record, f, indent=2)

    print(f"[Provenance Merge] Provenance ledger written to: {output_path}")
    return output_path