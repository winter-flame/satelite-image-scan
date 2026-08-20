"""
backend/postprocess/stitcher.py

Stitches processed GeoTIFF tiles back into a single continuous raster dataset
using 2D raised cosine windowing to eliminate seam artifacts.
"""

import os
import glob
from typing import List
import numpy as np
import rasterio
from rasterio.transform import from_bounds


def create_2d_raised_cosine_window(height: int, width: int) -> np.ndarray:
    """Generates a 2D smooth blending window for seamless tile stitching."""
    wy = np.hanning(height)
    wx = np.hanning(width)
    return np.outer(wy, wx)


def stitch_processed_tiles(
    tile_dir: str, 
    output_geotiff_path: str, 
    overlap_px: int = 32
) -> str:
    """
    Reads processed tile TIFs from tile_dir and reconstructs the full GeoTIFF.
    """
    tile_files = sorted(glob.glob(os.path.join(tile_dir, "*.tif")))
    if not tile_files:
        raise FileNotFoundError(f"No tile TIFs found in directory: {tile_dir}")

    # Read spatial reference from first tile
    with rasterio.open(tile_files[0]) as sample:
        crs = sample.crs
        count = sample.count
        dtype = sample.dtypes[0]

    # Calculate global bounding box & dimensions across all tiles
    min_x, min_y, max_x, max_y = float("inf"), float("inf"), float("-inf"), float("-inf")
    for tf in tile_files:
        with rasterio.open(tf) as src:
            b = src.bounds
            min_x, min_y = min(min_x, b.left), min(min_y, b.bottom)
            max_x, max_y = max(max_x, b.right), max(max_y, b.top)

    # Reconstruct combined output raster metadata
    with rasterio.open(tile_files[0]) as sample:
        pixel_size_x = abs(sample.transform.a)
        pixel_size_y = abs(sample.transform.e)

    out_width = int(round((max_x - min_x) / pixel_size_x))
    out_height = int(round((max_y - min_y) / pixel_size_y))
    out_transform = from_bounds(min_x, min_y, max_x, max_y, out_width, out_height)

    # Accumulator buffers for weighted blending
    acc_data = np.zeros((count, out_height, out_width), dtype=np.float32)
    acc_weights = np.zeros((out_height, out_width), dtype=np.float32)

    for tf in tile_files:
        with rasterio.open(tf) as src:
            data = src.read().astype(np.float32)
            h, w = src.height, src.width
            window_weights = create_2d_raised_cosine_window(h, w)

            # Compute pixel offset relative to output origin
            col_off = int(round((src.bounds.left - min_x) / pixel_size_x))
            row_off = int(round((max_y - src.bounds.top) / pixel_size_y))

            for b in range(count):
                acc_data[b, row_off:row_off+h, col_off:col_off+w] += data[b] * window_weights

            acc_weights[row_off:row_off+h, col_off:col_off+w] += window_weights

    # Normalize blended bands by weight sum
    mask = acc_weights > 0
    for b in range(count):
        acc_data[b, mask] /= acc_weights[mask]

    output_meta = {
        "driver": "GTiff",
        "height": out_height,
        "width": out_width,
        "count": count,
        "dtype": dtype,
        "crs": crs,
        "transform": out_transform
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_geotiff_path)), exist_ok=True)
    with rasterio.open(output_geotiff_path, "w", **output_meta) as dst:
        dst.write(np.clip(acc_data, 0, 255).astype(dtype))

    return output_geotiff_path