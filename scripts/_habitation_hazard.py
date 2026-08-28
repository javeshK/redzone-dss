"""Sample pipeline hazard rasters at habitation points and compute pct_red."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
from pyproj import Transformer
from shapely.geometry import Point

from _crs import COMPUTE_CRS, DISPLAY_CRS

HAB_BUFFER_M = 300.0

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


def sample_raster_at_point(raster_path: Path, lon: float, lat: float) -> float | None:
    if not HAS_RASTERIO or not raster_path.exists():
        return None
    with rasterio.open(raster_path) as src:
        transformer = Transformer.from_crs(DISPLAY_CRS, src.crs, always_xy=True)
        x, y = transformer.transform(lon, lat)
        row, col = src.index(x, y)
        if row < 0 or col < 0 or row >= src.height or col >= src.width:
            return None
        val = float(src.read(1)[row, col])
        if src.nodata is not None and val == src.nodata:
            return None
        if np.isnan(val):
            return None
        return float(np.clip(val, 0.0, 1.0))


def compute_pct_red(lon: float, lat: float, red_zones_path: Path, buffer_m: float = HAB_BUFFER_M) -> float:
    if not red_zones_path.exists():
        return 0.0
    rz = gpd.read_file(red_zones_path)
    if rz.empty or "zone_class" not in rz.columns:
        return 0.0

    hab = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs=DISPLAY_CRS).to_crs(COMPUTE_CRS)
    buffer = hab.geometry.iloc[0].buffer(buffer_m)
    buffer_area = buffer.area
    if buffer_area <= 0:
        return 0.0

    rz_utm = rz.to_crs(COMPUTE_CRS)
    red = rz_utm[rz_utm["zone_class"] == "Red"]
    if red.empty:
        return 0.0

    red_area = red.intersection(buffer).area.sum()
    return round(float(red_area / buffer_area * 100.0), 1)


def sample_habitation_hazards(
    lon: float,
    lat: float,
    paths: dict,
    repo_root: Path,
    fallback: dict | None = None,
) -> dict:
    """Return h_ls, h_ff, h and pct_red from pipeline rasters when available."""
    processed = paths["processed"]
    h_ls_path = repo_root / processed["h_ls"]
    h_ff_path = repo_root / processed["h_ff"]
    h_path = repo_root / processed["hazard_raster"]
    rz_path = repo_root / paths["out"]["red_zones"]

    h_ls = sample_raster_at_point(h_ls_path, lon, lat)
    h_ff = sample_raster_at_point(h_ff_path, lon, lat)
    h = sample_raster_at_point(h_path, lon, lat)

    if h is None and h_ls is not None and h_ff is not None:
        h = float(1.0 - (1.0 - h_ls) * (1.0 - h_ff))

    pct_red = compute_pct_red(lon, lat, rz_path)

    if fallback:
        h_ls = h_ls if h_ls is not None else fallback.get("h_ls")
        h_ff = h_ff if h_ff is not None else fallback.get("h_ff")
        h = h if h is not None else fallback.get("h")
        if pct_red == 0.0 and fallback.get("pct_red"):
            pct_red = fallback["pct_red"]

    return {
        "h_ls": h_ls,
        "h_ff": h_ff,
        "h": h,
        "pct_red": pct_red,
        "from_pipeline": h_ls is not None and h_ff is not None and h is not None,
    }
