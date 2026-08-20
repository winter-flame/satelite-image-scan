import json
import os

import numpy as np
import rasterio
def stitch_tiles_feathered(manifest_path: str, output_path: str) -> dict:
    """
    Reassembles tiles using distance-weighted feather blending instead of
    a hard first/last/min/max cutover -- eliminates visible seams at tile
    boundaries, at the cost of being slower and using more memory than
    stitch_tiles() since the full canvas is built explicitly.
    """
    from postprocess.blend import feather_blend_stack

    with open(manifest_path) as f:
        manifest = json.load(f)

    tiles_dir = os.path.dirname(manifest_path)
    tile_meta = manifest["tiles"]

    tile_arrays = []
    tile_offsets = []
    tile_valid_masks = []
    ref_profile = None

    for t in tile_meta:
        tile_path = os.path.join(tiles_dir, t["filename"])
        with rasterio.open(tile_path) as src:
            if ref_profile is None:
                ref_profile = src.profile.copy()
            data = src.read()
            nodata = src.nodata
            valid_mask = (data[0] != nodata) if nodata is not None else np.ones(data.shape[1:], dtype=bool)

            tile_arrays.append(data)
            tile_offsets.append((t["y"], t["x"]))
            tile_valid_masks.append(valid_mask)

    canvas_h = manifest["source_height"]
    canvas_w = manifest["source_width"]
    bands = tile_arrays[0].shape[0]

    blended = feather_blend_stack(
        tile_arrays, tile_offsets, tile_valid_masks,
        canvas_shape=(bands, canvas_h, canvas_w),
    )

    with rasterio.open(tile_meta[0]["filename"] and os.path.join(tiles_dir, tile_meta[0]["filename"])) as first_tile:
        first_transform = first_tile.transform

    # Reconstruct the full-extent transform from the first tile's pixel scale,
    # anchored at the manifest's recorded source origin (0,0 tile position).
    from rasterio.transform import Affine
    full_transform = Affine(
        first_transform.a, first_transform.b, first_transform.c - (tile_meta[0]["x"] * first_transform.a),
        first_transform.d, first_transform.e, first_transform.f - (tile_meta[0]["y"] * first_transform.e),
    )

    out_profile = ref_profile.copy()
    out_profile.update({
        "height": canvas_h,
        "width": canvas_w,
        "transform": full_transform,
    })

    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(blended)

    return {
        "output_path": output_path,
        "width": canvas_w,
        "height": canvas_h,
        "crs": str(out_profile.get("crs")),
        "transform": list(full_transform)[:6],
        "tile_count": len(tile_meta),
        "method": "feathered",
    }