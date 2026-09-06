"""Rudraprayag district boundary helpers."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union

from _crs import DISPLAY_CRS, to_display

DISTRICT_LABEL = "Rudraprayag"


def filter_rudraprayag(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Keep only Rudraprayag; dissolve multi-part to one row."""
    if gdf.empty:
        return gdf
    if gdf.crs is None:
        gdf = gdf.set_crs(DISPLAY_CRS)
    gdf = to_display(gdf)

    matched = gdf.iloc[0:0]
    for col in gdf.columns:
        if col == "geometry":
            continue
        try:
            mask = gdf[col].astype(str).str.contains(DISTRICT_LABEL, case=False, na=False)
            if mask.any():
                matched = gdf[mask]
                break
        except (TypeError, ValueError):
            continue

    if matched.empty and len(gdf) > 5:
        # Whole-country ADM dump — fall back to configured bbox
        return bbox_fallback_gdf()

    if matched.empty:
        matched = gdf

    if len(matched) > 1:
        geom = unary_union(matched.geometry)
        return gpd.GeoDataFrame(
            [{"name": DISTRICT_LABEL, "state": "Uttarakhand", "district_code": "UT_RUD"}],
            geometry=[geom],
            crs=DISPLAY_CRS,
        )

    row = matched.iloc[[0]].copy()
    row["name"] = DISTRICT_LABEL
    row["state"] = "Uttarakhand"
    row["district_code"] = "UT_RUD"
    return row


def bbox_fallback_gdf(bbox: dict | None = None) -> gpd.GeoDataFrame:
    from _config import load_paths

    b = bbox or load_paths()["bbox"]
    geom = box(b["min_lon"], b["min_lat"], b["max_lon"], b["max_lat"])
    return gpd.GeoDataFrame(
        [{"name": DISTRICT_LABEL, "state": "Uttarakhand", "district_code": "UT_RUD", "source": "BBOX_FALLBACK"}],
        geometry=[geom],
        crs=DISPLAY_CRS,
    )
