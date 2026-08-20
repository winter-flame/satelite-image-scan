"""
Extracts imaging metadata from GeoTIFF/PDS4 files and derives routing
hints for which AI model/pipeline should process the tile set.

Real satellite files vary wildly in what metadata they actually embed —
some have rich EXIF/XML tags, some have almost nothing beyond raster
dimensions. This module pulls what's available and falls back to safe
defaults everywhere else, rather than failing on incomplete data.
"""

from dataclasses import dataclass, asdict
from typing import Optional
import rasterio


@dataclass
class ImageMetadata:
    band_count: int
    dtype: str
    width: int
    height: int
    crs: Optional[str]
    resolution_x: Optional[float]
    resolution_y: Optional[float]
    sensor_hint: Optional[str]          # best-effort guess, e.g. "multispectral", "panchromatic"
    sun_elevation_deg: Optional[float]  # from tags, if present
    nodata_value: Optional[float]
    raw_tags: dict                      # everything else found, for debugging/manual inspection


@dataclass
class RoutingHints:
    pipeline: str            # which ml_engine pipeline to route to
    reason: str               # human-readable explanation of the decision
    confidence: str           # "high" | "medium" | "low" — how sure we are about the routing


def extract_metadata(file_path: str) -> ImageMetadata:
    with rasterio.open(file_path) as src:
        tags = src.tags()
        band_tags = src.tags(1) if src.count >= 1 else {}

        sun_elevation = _parse_float(
            tags.get("SUN_ELEVATION")
            or tags.get("sun_elevation")
            or band_tags.get("SUN_ELEVATION")
        )

        sensor_hint = _guess_sensor(src.count, src.dtypes[0] if src.dtypes else None, tags)

        return ImageMetadata(
            band_count=src.count,
            dtype=str(src.dtypes[0]) if src.dtypes else "unknown",
            width=src.width,
            height=src.height,
            crs=str(src.crs) if src.crs else None,
            resolution_x=abs(src.transform.a) if src.transform else None,
            resolution_y=abs(src.transform.e) if src.transform else None,
            sensor_hint=sensor_hint,
            sun_elevation_deg=sun_elevation,
            nodata_value=src.nodata,
            raw_tags=tags,
        )


def _parse_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _guess_sensor(band_count: int, dtype: Optional[str], tags: dict) -> str:
    """
    Best-effort sensor classification. Real routing should eventually
    read explicit sensor tags (e.g. from PDS4 labels) when available —
    this heuristic is a fallback for files that don't declare it.
    """
    declared = tags.get("SENSOR") or tags.get("INSTRUMENT") or tags.get("sensor")
    if declared:
        return str(declared)

    if band_count == 1:
        return "panchromatic"
    if band_count in (3, 4):
        return "multispectral"
    if band_count > 4:
        return "hyperspectral"
    return "unknown"


def derive_routing_hints(meta: ImageMetadata) -> RoutingHints:
    """
    Maps extracted metadata to a target ml_engine pipeline.
    This is intentionally simple — extend as ml_engine adds more
    specialized model variants (e.g. per-sensor fine-tunes).
    """
    if meta.sensor_hint == "panchromatic":
        return RoutingHints(
            pipeline="sr_panchromatic",
            reason="Single-band input detected; routing to panchromatic SR model.",
            confidence="high",
        )

    if meta.sensor_hint == "hyperspectral":
        return RoutingHints(
            pipeline="sr_hyperspectral",
            reason=f"{meta.band_count} bands detected; routing to hyperspectral pipeline.",
            confidence="medium",
        )

    if meta.sensor_hint == "multispectral":
        confidence = "high" if meta.sun_elevation_deg is not None else "medium"
        reason = f"{meta.band_count}-band multispectral input detected."
        if meta.sun_elevation_deg is not None:
            reason += f" Sun elevation {meta.sun_elevation_deg}° available for illumination correction."
        return RoutingHints(pipeline="sr_multispectral", reason=reason, confidence=confidence)

    return RoutingHints(
        pipeline="sr_default",
        reason="Could not confidently classify sensor type from available metadata; using default pipeline.",
        confidence="low",
    )


def extract_and_route(file_path: str) -> dict:
    """Convenience entry point: extract metadata and return both the
    metadata and routing hints as a single JSON-serializable dict."""
    meta = extract_metadata(file_path)
    hints = derive_routing_hints(meta)
    return {
        "metadata": asdict(meta),
        "routing": asdict(hints),
    }
