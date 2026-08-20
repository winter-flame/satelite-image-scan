"""
backend/ingest_api/validators.py

Validation utilities for uploaded GeoTIFF files. Checks raster format integrity,
band count thresholds, Coordinate Reference System (CRS) presence, and dimension caps.
"""

import os
from typing import Dict, Any
import rasterio

# Configurable validation constraints
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 2000))  # 2 GB cap
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", 30000))  # Max width/height in px
MIN_BAND_COUNT = 1
MAX_BAND_COUNT = 16  # Supports RGB, Multispectral (Sentinel-2/Landsat)


def validate_geotiff(file_path: str) -> Dict[str, Any]:
    """
    Validates an uploaded GeoTIFF file against size, header, band, and CRS limits.

    Args:
        file_path (str): Local path to the uploaded file.

    Returns:
        Dict[str, Any]: Dictionary containing 'is_valid' boolean, error message if any,
                        and extracted header metadata.
    """
    if not os.path.exists(file_path):
        return {"is_valid": False, "error": f"File not found at path: {file_path}"}

    # 1. File Size Validation
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return {
            "is_valid": False, 
            "error": f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_FILE_SIZE_MB} MB."
        }

    # 2. Raster Header & GDAL Format Integrity Validation
    try:
        with rasterio.open(file_path) as src:
            width = src.width
            height = src.height
            count = src.count
            crs = src.crs
            driver = src.driver

            # Check format driver
            if driver != "GTiff":
                return {
                    "is_valid": False, 
                    "error": f"Unsupported raster driver '{driver}'. Must be a standard GeoTIFF ('GTiff')."
                }

            # 3. Band Count Constraints
            if count < MIN_BAND_COUNT or count > MAX_BAND_COUNT:
                return {
                    "is_valid": False, 
                    "error": f"Unsupported band count ({count}). Must be between {MIN_BAND_COUNT} and {MAX_BAND_COUNT} bands."
                }

            # 4. Maximum Dimension Caps
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                return {
                    "is_valid": False, 
                    "error": f"Image dimensions ({width}x{height}px) exceed maximum cap of {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}px."
                }

            # 5. Coordinate Reference System (CRS) Presence Check
            if not crs:
                return {
                    "is_valid": False, 
                    "error": "Missing Spatial Reference / CRS metadata in GeoTIFF header."
                }

            # Validation succeeded — return raster metadata
            return {
                "is_valid": True,
                "error": None,
                "metadata": {
                    "width": width,
                    "height": height,
                    "bands": count,
                    "crs": str(crs),
                    "driver": driver,
                    "size_mb": round(file_size_mb, 2)
                }
            }

    except rasterio.errors.RasterioIOError:
        return {
            "is_valid": False, 
            "error": "Corrupted or unreadable GeoTIFF file header."
        }
    except Exception as e:
        return {
            "is_valid": False, 
            "error": f"Unexpected validation failure: {str(e)}"
        }