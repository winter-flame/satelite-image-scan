"""
backend/tiler/tile_cutter.py

Slices an input GeoTIFF into overlapping sub-tiles (512x512 with 32px overlap)
and extracts geographic bounding box metadata for each tile.
"""

import os
from typing import List, Dict, Any
import numpy as np
import rasterio
from rasterio.windows import Window

def slice_geotiff(
    input_path: str,
    output_dir: str,
    tile_size: int = 512,
    overlap_px: int = 32
) -> List[Dict[str, Any]]:
    """
    Cuts a GeoTIFF into overlapping tiles and saves them to disk.

    Args:
        input_path (str): Path to the source GeoTIFF.
        output_dir (str): Directory where individual tile TIFs will be written.
        tile_size (int): Tile dimensions in pixels (default: 512).
        overlap_px (int): Pixel overlap along edges (default: 32).

    Returns:
        List[Dict[str, Any]]: Manifest containing tile file paths, grid indices, 
                             and geographic bounding boxes.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input GeoTIFF not found at: {input_path}")

    os.makedirs(output_dir, exist_ok=True)
    step_size = tile_size - overlap_px
    manifest = []

    with rasterio.open(input_path) as src:
        width = src.width
        height = src.height
        crs = src.crs
        transform = src.transform
        count = src.count
        dtype = src.dtypes[0]

        # Calculate grid bounds
        max_rows = max(1, int(np.ceil((height - overlap_px) / step_size)))
        max_cols = max(1, int(np.ceil((width - overlap_px) / step_size)))

        for r in range(max_rows):
            for c in range(max_cols):
                y_start = r * step_size
                x_start = c * step_size

                # Handle edge clipping if remaining dimensions are smaller than tile_size
                win_w = min(tile_size, width - x_start)
                win_h = min(tile_size, height - y_start)

                if win_w <= 0 or win_h <= 0:
                    continue

                window = Window(x_start, y_start, win_w, win_h)
                tile_transform = rasterio.windows.transform(window, transform)
                
                # Calculate geographic bounding box for this tile
                bounds = rasterio.windows.bounds(window, transform)

                tile_filename = f"tile_{r}_{c}.tif"
                tile_filepath = os.path.join(output_dir, tile_filename)

                # Write individual GeoTIFF tile
                tile_data = src.read(window=window)

                tile_meta = {
                    "driver": "GTiff",
                    "height": win_h,
                    "width": win_w,
                    "count": count,
                    "dtype": dtype,
                    "crs": crs,
                    "transform": tile_transform
                }

                with rasterio.open(tile_filepath, "w", **tile_meta) as dst:
                    dst.write(tile_data)

                manifest.append({
                    "tile_name": tile_filename,
                    "file_path": tile_filepath,
                    "row": r,
                    "col": c,
                    "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                    "crs": str(crs)
                })

    print(f"[Tile Cutter] Successfully generated {len(manifest)} tiles in: {output_dir}")
    return manifest