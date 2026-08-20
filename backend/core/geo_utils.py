"""
Tiling and stitching utilities for large satellite/planetary imagery.
Uses Rasterio so georeferencing (CRS, transform) is preserved per tile —
unlike a plain image-library slicer, tiles here stay usable for mapping.
"""

import os
import json
from typing import List, Dict
import rasterio
from rasterio.windows import Window


def compute_origins(total: int, tile_size: int, overlap: int) -> List[int]:
    """Tile origin coordinates along one axis, with the final tile
    clamped flush to the edge so every tile is a consistent full size."""
    if total <= tile_size:
        return [0]

    stride = tile_size - overlap
    origins = []
    pos = 0
    while pos + tile_size < total:
        origins.append(pos)
        pos += stride
    origins.append(total - tile_size)

    return sorted(set(origins))


def slice_geotiff(
    input_path: str,
    output_dir: str,
    tile_size: int = 512,
    overlap: int = 64,
) -> Dict:
    """
    Slices a (Geo)TIFF into tile_size x tile_size tiles with overlap,
    preserving CRS/transform per tile. Writes a manifest.json alongside
    the tiles for later stitching or georeferenced lookups.
    """
    os.makedirs(output_dir, exist_ok=True)

    with rasterio.open(input_path) as src:
        width, height = src.width, src.height
        x_origins = compute_origins(width, tile_size, overlap)
        y_origins = compute_origins(height, tile_size, overlap)

        manifest = {
            "source": input_path,
            "source_width": width,
            "source_height": height,
            "tile_size": tile_size,
            "overlap": overlap,
            "crs": str(src.crs) if src.crs else None,
            "tiles": [],
        }

        index = 0
        for y in y_origins:
            for x in x_origins:
                window = Window(x, y, tile_size, tile_size)
                transform = src.window_transform(window)
                data = src.read(window=window)

                filename = f"tile_{index:05d}_x{x}_y{y}.tif"
                out_path = os.path.join(output_dir, filename)

                profile = src.profile.copy()
                profile.update({
                    "height": tile_size,
                    "width": tile_size,
                    "transform": transform,
                })

                with rasterio.open(out_path, "w", **profile) as dst:
                    dst.write(data)

                manifest["tiles"].append({
                    "index": index,
                    "filename": filename,
                    "x": x,
                    "y": y,
                    "width": tile_size,
                    "height": tile_size,
                })
                index += 1

        manifest["tile_count"] = index

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def stitch_tiles(manifest_path: str, output_path: str) -> str:
    """
    Reassembles tiles listed in a manifest.json back into a single
    georeferenced image, using each tile's recorded (x, y) origin.
    NOTE: placeholder — full mosaic logic (handling overlap blending)
    should be filled in once real detection output needs to be stitched.
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    # TODO: implement real stitching (e.g. via rasterio.merge.merge)
    raise NotImplementedError("stitch_tiles is a placeholder — implement when needed")
