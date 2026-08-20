"""
Feathered (distance-weighted) blending for seamless tile mosaics.

Hard-cutover merging (first/last/min/max) leaves visible seams at tile
boundaries because pixel values can jump abruptly at the cutover line.
Feathering instead weights each tile's contribution by its distance from
the tile's own edge -- pixels near a tile's center are trusted fully,
pixels near its edge are blended smoothly with the neighboring tile's
edge pixels, so the seam disappears.
"""

import numpy as np
from scipy.ndimage import distance_transform_edt


def edge_distance_weights(height: int, width: int, mask: np.ndarray = None) -> np.ndarray:
    """
    Returns a (height, width) float array where each pixel's value is its
    distance to the nearest edge (or nodata boundary), normalized to [0, 1].
    Used as a blending weight: high in the tile's interior, tapering to 0
    at its border.
    """
    if mask is None:
        mask = np.ones((height, width), dtype=bool)

    # distance_transform_edt gives distance to nearest zero/False pixel,
    # so invert the mask to measure distance inward from the tile boundary
    dist = distance_transform_edt(mask)

    max_dist = dist.max()
    if max_dist == 0:
        return np.ones((height, width), dtype=np.float32)

    return (dist / max_dist).astype(np.float32)


def feather_blend_stack(tile_arrays: list, tile_offsets: list, tile_valid_masks: list, canvas_shape: tuple) -> np.ndarray:
    """
    Blends a list of tile pixel arrays onto a shared canvas using
    distance-weighted feathering.

    tile_arrays: list of (bands, h, w) arrays, one per tile
    tile_offsets: list of (row_offset, col_offset) placing each tile on the canvas
    tile_valid_masks: list of (h, w) boolean arrays marking valid (non-nodata) pixels per tile
    canvas_shape: (bands, canvas_height, canvas_width)

    Returns the blended (bands, canvas_height, canvas_width) array.
    """
    bands, canvas_h, canvas_w = canvas_shape
    accumulator = np.zeros((bands, canvas_h, canvas_w), dtype=np.float64)
    weight_sum = np.zeros((canvas_h, canvas_w), dtype=np.float64)

    for arr, (row_off, col_off), valid_mask in zip(tile_arrays, tile_offsets, tile_valid_masks):
        _, h, w = arr.shape
        weights = edge_distance_weights(h, w, mask=valid_mask)

        row_end = row_off + h
        col_end = col_off + w

        for b in range(bands):
            accumulator[b, row_off:row_end, col_off:col_end] += arr[b].astype(np.float64) * weights

        weight_sum[row_off:row_end, col_off:col_end] += weights

    # avoid divide-by-zero where no tile covered a pixel
    safe_weight_sum = np.where(weight_sum == 0, 1, weight_sum)
    blended = accumulator / safe_weight_sum

    return blended.astype(tile_arrays[0].dtype) if tile_arrays else accumulator.astype(np.float32)
