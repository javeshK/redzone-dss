"""Scenario rescoring — rainfall factor scaling on cached hazard components."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from _config import REPO_ROOT, load_paths, load_weights
from _crs import normalize_0_1
from _scoring import classify_zone, compute_h_ff, compute_h_ls, compute_multi_hazard

try:
    import rasterio
    from rasterio.features import geometry_mask
    import geopandas as gpd
    from _crs import COMPUTE_CRS, DISPLAY_CRS, to_compute
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

ALLOWED_FACTORS = (1.0, 1.2, 1.5)


def _load_base_components(paths: dict) -> dict[str, Any] | None:
    if not HAS_RASTERIO:
        return None
    slope_path = REPO_ROOT / paths["processed"]["slope"]
    kde_path = REPO_ROOT / paths["processed"]["kde_landslide"]
    rainfall_path = REPO_ROOT / paths["raw"]["rainfall"]
    twi_path = REPO_ROOT / paths["processed"]["twi"]
    stream_dist_path = REPO_ROOT / paths["processed"]["stream_dist"]
    dem_path = REPO_ROOT / paths["processed"]["dem_clipped"]
    district_path = REPO_ROOT / paths["out"]["district"]

    if not all(p.exists() for p in (slope_path, dem_path, district_path)):
        return None

    district = gpd.read_file(district_path)
    with rasterio.open(dem_path) as src:
        profile = src.profile.copy()
        mask_arr = geometry_mask(
            [g for g in to_compute(district).geometry if g is not None],
            out_shape=(src.height, src.width),
            transform=src.transform,
            invert=True,
        )

    def _read(path: Path) -> np.ndarray:
        with rasterio.open(path) as src:
            arr = src.read(1).astype(float)
            arr[arr == src.nodata] = np.nan
            return arr

    slope_deg = _read(slope_path)
    slope_s = np.clip((slope_deg - 15.0) / 30.0, 0.0, 1.0)
    kde = _read(kde_path) if kde_path.exists() else np.zeros_like(slope_deg)
    twi = _read(twi_path) if twi_path.exists() else np.zeros_like(slope_deg)
    dist_m = _read(stream_dist_path) if stream_dist_path.exists() else np.full_like(slope_deg, 1000.0)

    rainfall = np.full_like(slope_deg, 0.5)
    has_rainfall = False
    if rainfall_path.exists():
        with rasterio.open(rainfall_path) as src:
            from rasterio.warp import reproject, Resampling
            dest = np.full((profile["height"], profile["width"]), np.nan, dtype="float32")
            reproject(
                source=rasterio.band(src, 1),
                destination=dest,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=profile["transform"],
                dst_crs=profile["crs"],
                resampling=Resampling.bilinear,
            )
            if np.nanmax(dest) > np.nanmin(dest):
                rainfall = dest
                has_rainfall = True

    stream_prox = np.clip(1.0 - dist_m / 1000.0, 0.0, 1.0)
    twi_norm = normalize_0_1(np.nan_to_num(twi, nan=np.nanmin(twi)))
    wetness = 0.5 * stream_prox + 0.5 * twi_norm

    for arr in (slope_s, kde, rainfall, wetness):
        arr[~mask_arr] = np.nan

    return {
        "slope_s": slope_s,
        "kde": kde,
        "rainfall": rainfall,
        "wetness": wetness,
        "has_rainfall": has_rainfall,
        "mask": mask_arr,
    }


def compute_scenario_hazard(factor: float, weights: dict | None = None, paths: dict | None = None) -> dict:
    """Recompute H_ls, H_ff, H with scaled rainfall factor."""
    if factor not in ALLOWED_FACTORS:
        raise ValueError(f"factor must be one of {ALLOWED_FACTORS}")
    weights = weights or load_weights()
    paths = paths or load_paths()
    comp = _load_base_components(paths)
    if comp is None:
        return {"factor": factor, "error": "processed rasters unavailable", "habitations": []}

    r_scaled = np.clip(comp["rainfall"] * factor, 0.0, 1.0)
    ls_w = weights["hazard"]["landslide"]
    ff_w = weights["hazard"]["flash_flood"]

    if comp["has_rainfall"]:
        h_ls = ls_w["slope"] * comp["slope_s"] + ls_w["landslide_density"] * comp["kde"] + ls_w["rainfall"] * r_scaled
        h_ff = ff_w["wetness_stream"] * comp["wetness"] + ff_w["rainfall"] * r_scaled
    else:
        ls_total = ls_w["slope"] + ls_w["landslide_density"]
        h_ls = (ls_w["slope"] / ls_total) * comp["slope_s"] + (ls_w["landslide_density"] / ls_total) * comp["kde"]
        h_ff = comp["wetness"]

    h = 1.0 - (1.0 - h_ls) * (1.0 - h_ff)
    h_ls = np.clip(h_ls, 0, 1)
    h_ff = np.clip(h_ff, 0, 1)
    h = np.clip(h, 0, 1)

    hab_path = REPO_ROOT / paths["out"]["habitations"]
    hab_results = []
    if hab_path.exists():
        from pyproj import Transformer
        habs = json.loads(hab_path.read_text(encoding="utf-8"))
        with rasterio.open(REPO_ROOT / paths["processed"]["dem_clipped"]) as src:
            transformer = Transformer.from_crs(DISPLAY_CRS, src.crs, always_xy=True)
            for feat in habs.get("features", []):
                props = feat["properties"]
                lon, lat = feat["geometry"]["coordinates"]
                x, y = transformer.transform(lon, lat)
                row, col = src.index(x, y)
                if 0 <= row < h.shape[0] and 0 <= col < h.shape[1]:
                    h_val = float(h[row, col]) if not np.isnan(h[row, col]) else props.get("h", 0)
                    h_ls_val = float(h_ls[row, col]) if not np.isnan(h_ls[row, col]) else props.get("h_ls", 0)
                    h_ff_val = float(h_ff[row, col]) if not np.isnan(h_ff[row, col]) else props.get("h_ff", 0)
                else:
                    h_val, h_ls_val, h_ff_val = props.get("h", 0), props.get("h_ls", 0), props.get("h_ff", 0)
                hab_results.append({
                    "id": props["id"],
                    "name": props["name"],
                    "h_ls": round(h_ls_val, 4),
                    "h_ff": round(h_ff_val, 4),
                    "h": round(h_val, 4),
                    "zone_class": classify_zone(h_val, weights),
                })

    valid_h = h[comp["mask"] & ~np.isnan(h)]
    return {
        "factor": factor,
        "rainfall_factor": factor,
        "has_rainfall": comp["has_rainfall"],
        "h_min": round(float(np.nanmin(valid_h)), 4) if len(valid_h) else 0,
        "h_max": round(float(np.nanmax(valid_h)), 4) if len(valid_h) else 0,
        "h_mean": round(float(np.nanmean(valid_h)), 4) if len(valid_h) else 0,
        "habitations": hab_results,
        "note": f"Scenario mode: rainfall scaled by {factor}x for decision-support exploration only",
    }


def export_scenarios(paths: dict | None = None) -> dict:
    """Precompute scenario summaries for all allowed factors."""
    paths = paths or load_paths()
    scenarios = {}
    for factor in ALLOWED_FACTORS:
        scenarios[str(factor)] = compute_scenario_hazard(factor, paths=paths)
    out_path = REPO_ROOT / paths["out_dir"] / "scenarios.json"
    out_path.write_text(json.dumps(scenarios, indent=2), encoding="utf-8")
    return scenarios
