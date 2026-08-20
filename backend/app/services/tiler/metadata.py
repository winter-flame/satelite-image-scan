"""
backend/tiler/metadata.py

Spatial metadata utilities for inspecting GeoTIFF headers, extracting bounding boxes,
converting spatial coordinate reference systems (CRS), and generating job summaries.
"""

from typing import Dict, Any, Tuple
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform_bounds


def extract_geotiff_metadata(file_path: str) -> Dict[str, Any]:
    """
    Reads GeoTIFF header information and extracts key spatial attributes.
    """
    with rasterio.open(file_path) as src:
        bounds = src.bounds
        crs = src.crs

        # Convert native bounding box to WGS84 (EPSG:4326) for API & UI displays
        wgs84_bounds = convert_bounds_crs(
            bounds=(bounds.left, bounds.bottom, bounds.right, bounds.top),
            src_crs=crs,
            dst_crs=CRS.from_epsg(4326)
        )

        return {
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": str(src.dtypes[0]),
            "crs": str(crs),
            "is_valid_crs": crs is not None,
            "bounds_native": [bounds.left, bounds.bottom, bounds.right, bounds.top],
            "bounds_wgs84": wgs84_bounds,
            "resolution": [abs(src.transform.a), abs(src.transform.e)]
        }


def convert_bounds_crs(
    bounds: Tuple[float, float, float, float], 
    src_crs: CRS, 
    dst_crs: CRS = CRS.from_epsg(4326)
) -> Tuple[float, float, float, float]:
    """
    Reprojects bounding box coordinates from source CRS to a target CRS (defaults to EPSG:4326).
    """
    if not src_crs:
        return bounds

    if src_crs == dst_crs:
        return bounds

    try:
        left, bottom, right, top = transform_bounds(src_crs, dst_crs, *bounds)
        return (round(left, 6), round(bottom, 6), round(right, 6), round(top, 6))
    except Exception as e:
        print(f"[Metadata] CRS transformation warning: {e}")
        return bounds


def calculate_grid_dimensions(
    width: int, 
    height: int, 
    tile_size: int = 512, 
    overlap_px: int = 32
) -> Tuple[int, int, int]:
    """
    Calculates total row count, column count, and total tile count for slicing.
    """
    step_size = tile_size - overlap_px
    cols = max(1, (width - overlap_px + step_size - 1) // step_size)
    rows = max(1, (height - overlap_px + step_size - 1) // step_size)
    total_tiles = rows * cols
    return rows, cols, total_tiles