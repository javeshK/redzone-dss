"""CRS helpers and validation for RedZone DSS GIS pipeline."""

from __future__ import annotations

import warnings

import geopandas as gpd
from pyproj import CRS

DISPLAY_CRS = "EPSG:4326"
COMPUTE_CRS = "EPSG:32644"

# Rudraprayag approximate bounds in UTM 44N (meters)
UTM_BOUNDS = {
    "min_x": 200000,
    "max_x": 350000,
    "min_y": 3320000,
    "max_y": 3420000,
}


def get_display_crs() -> CRS:
    return CRS.from_user_input(DISPLAY_CRS)


def get_compute_crs() -> CRS:
    return CRS.from_user_input(COMPUTE_CRS)


def to_display(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS — cannot reproject safely")
    return gdf.to_crs(DISPLAY_CRS)


def to_compute(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS — cannot reproject safely")
    return gdf.to_crs(COMPUTE_CRS)


def validate_utm_geometry(gdf: gpd.GeoDataFrame, label: str = "layer") -> None:
    """Reject geometries that look like degrees interpreted as meters."""
    if gdf.crs is None:
        raise ValueError(f"{label}: missing CRS")
    crs_str = gdf.crs.to_string()
    if crs_str == DISPLAY_CRS:
        bounds = gdf.total_bounds
        # Suspicious if extent < 0.01 degrees (~1 km) — likely CRS mislabeling
        if (bounds[2] - bounds[0] < 0.01) and (bounds[3] - bounds[1] < 0.01):
            raise ValueError(
                f"{label}: geometry extent too small in EPSG:4326 — "
                "possible CRS misinterpretation"
            )
    elif crs_str == COMPUTE_CRS:
        bounds = gdf.total_bounds
        if bounds[0] < 0 or bounds[1] < 0:
            warnings.warn(f"{label}: negative UTM coordinates — check CRS")


def normalize_0_1(arr, vmin=None, vmax=None):
    """Normalize array to [0, 1]."""
    import numpy as np

    a = np.asarray(arr, dtype=float)
    lo = vmin if vmin is not None else np.nanmin(a)
    hi = vmax if vmax is not None else np.nanmax(a)
    if hi - lo < 1e-9:
        return np.zeros_like(a)
    return np.clip((a - lo) / (hi - lo), 0, 1)
