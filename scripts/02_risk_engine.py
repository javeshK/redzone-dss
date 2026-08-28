#!/usr/bin/env python3
"""02_risk_engine.py — H_ls, H_ff, H, red-zone classification and polygonization."""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from scipy import ndimage
from shapely.geometry import shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths, load_weights
from _crs import COMPUTE_CRS, DISPLAY_CRS, normalize_0_1, to_compute, to_display
from _scoring import classify_zone, compute_h_ff, compute_h_ls, compute_multi_hazard

try:
    import rasterio
    from rasterio.features import geometry_mask, shapes
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

MIN_ZONE_AREA_HA = 2.0
SIMPLIFY_TOLERANCE_M = 75.0
MAX_VERTICES = 500
STREAM_PROX_CAP_M = 1000.0
KDE_BANDWIDTH_M = 500.0
ZONE_CLASS_TO_INT = {"Yellow": 1, "Orange": 2, "Red": 3}
INT_TO_ZONE_CLASS = {v: k for k, v in ZONE_CLASS_TO_INT.items()}


def load_landslides(paths: dict, district: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, str]:
    ls_path = REPO_ROOT / paths["raw"]["landslides"]
    out_path = REPO_ROOT / paths["out"]["landslides"]
    provenance = "DERIVED"
    if ls_path.exists():
        gdf = gpd.read_file(ls_path)
        if gdf.crs is None:
            gdf = gdf.set_crs(DISPLAY_CRS)
        gdf = gpd.clip(gdf, district)
        if len(gdf) > 0:
            gdf["source"] = "OPEN_DATA"
            gdf.to_file(out_path, driver="GeoJSON")
            return gdf, "OPEN_DATA"
    if out_path.exists():
        gdf = gpd.read_file(out_path)
        if len(gdf) > 0:
            return gdf, gdf.iloc[0].get("source", "OPEN_DATA")
    return gpd.GeoDataFrame(geometry=[], crs=DISPLAY_CRS), provenance


def read_masked_raster(path: Path, mask_arr: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1).astype(float)
        arr[arr == src.nodata] = np.nan
        arr[~mask_arr] = np.nan
        return arr, src.profile


def slope_severity(slope_deg: np.ndarray) -> np.ndarray:
    """S = clip((slope° - 15) / 30, 0, 1) per spec §5.1."""
    return np.clip((slope_deg - 15.0) / 30.0, 0.0, 1.0)


def stream_proximity_score(dist_m: np.ndarray) -> np.ndarray:
    """Inverse distance to stream capped at 1 km."""
    return np.clip(1.0 - dist_m / STREAM_PROX_CAP_M, 0.0, 1.0)


def kde_landslide_raster(
    landslides: gpd.GeoDataFrame,
    profile: dict,
    mask_arr: np.ndarray,
    slope_deg: np.ndarray,
) -> tuple[np.ndarray, str]:
    """KDE from GSI points (~500 m bandwidth) or slope > 30° proxy fallback."""
    rows, cols = mask_arr.shape
    density = np.zeros((rows, cols), dtype=float)
    transform = profile["transform"]

    if len(landslides) > 0:
        ls_utm = to_compute(landslides)
        sigma_cells = max(KDE_BANDWIDTH_M / abs(transform.a), 1.0)
        for geom in ls_utm.geometry:
            if geom is None or geom.is_empty:
                continue
            col = int((geom.centroid.x - transform.c) / transform.a)
            row = int((geom.centroid.y - transform.f) / transform.e)
            if 0 <= row < rows and 0 <= col < cols:
                density[row, col] += 1.0
        if density.max() > 0:
            density = ndimage.gaussian_filter(density, sigma=sigma_cells)
            density = np.where(mask_arr, density, np.nan)
            return normalize_0_1(density), "OPEN_DATA"

    print("  [warn] No landslide points — using slope > 30° proxy (DERIVED)")
    proxy = np.clip((slope_deg - 30.0) / 15.0, 0.0, 1.0)
    return np.where(mask_arr, proxy, np.nan), "DERIVED"


def load_rainfall_raster(
    paths: dict, profile: dict, mask_arr: np.ndarray
) -> tuple[np.ndarray, bool]:
    rain_path = REPO_ROOT / paths["raw"]["rainfall"]
    if rain_path.exists() and HAS_RASTERIO:
        with rasterio.open(rain_path) as src:
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
            dest[~mask_arr] = np.nan
            if np.nanmax(dest) > np.nanmin(dest):
                return normalize_0_1(dest), True
    print("  [warn] Rainfall raster missing — using uniform R=0.5 (SYNTHETIC, degraded)")
    r = np.where(mask_arr, 0.5, np.nan)
    return r, False


def wetness_signal(stream_prox: np.ndarray, twi: np.ndarray) -> np.ndarray:
    twi_norm = normalize_0_1(np.nan_to_num(twi, nan=np.nanmin(twi)))
    return 0.5 * stream_prox + 0.5 * twi_norm


def compute_hazard_arrays(
    slope_deg: np.ndarray,
    landslide_kde: np.ndarray,
    rainfall: np.ndarray,
    wetness: np.ndarray,
    weights: dict,
    has_rainfall: bool,
    mask_arr: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    s = slope_severity(slope_deg)
    l = landslide_kde
    r = rainfall
    w = wetness

    ls_w = weights["hazard"]["landslide"]
    ff_w = weights["hazard"]["flash_flood"]

    if has_rainfall:
        h_ls = ls_w["slope"] * s + ls_w["landslide_density"] * l + ls_w["rainfall"] * r
        h_ff = ff_w["wetness_stream"] * w + ff_w["rainfall"] * r
    else:
        ls_total = ls_w["slope"] + ls_w["landslide_density"]
        h_ls = (ls_w["slope"] / ls_total) * s + (ls_w["landslide_density"] / ls_total) * l
        h_ff = w

    h = 1.0 - (1.0 - h_ls) * (1.0 - h_ff)
    h_ls = np.where(mask_arr, h_ls, np.nan)
    h_ff = np.where(mask_arr, h_ff, np.nan)
    h = np.where(mask_arr, h, np.nan)
    return h_ls, h_ff, h


def classify_raster(h: np.ndarray, weights: dict, mask_arr: np.ndarray) -> np.ndarray:
    classes = weights["red_zone_classes"]
    zone_int = np.zeros(h.shape, dtype=np.uint8)
    valid = mask_arr & ~np.isnan(h)
    zone_int[valid & (h >= classes["red"])] = ZONE_CLASS_TO_INT["Red"]
    zone_int[valid & (h >= classes["orange"]) & (h < classes["red"])] = ZONE_CLASS_TO_INT["Orange"]
    zone_int[valid & (h >= classes["yellow"]) & (h < classes["orange"])] = ZONE_CLASS_TO_INT["Yellow"]
    return zone_int


def write_hazard_raster(path: Path, h: np.ndarray, profile: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = np.where(np.isnan(h), -9999, h).astype("float32")
    prof = profile.copy()
    prof.update(dtype="float32", count=1, nodata=-9999)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(out, 1)


def simplify_geometry(geom, tolerance: float = SIMPLIFY_TOLERANCE_M, max_vertices: int = MAX_VERTICES):
    """Douglas-Peucker simplify with a vertex budget per spec §4 R4."""
    from shapely.geometry import MultiPolygon, Polygon

    def _simplify_poly(poly: Polygon) -> Polygon:
        t = tolerance
        simplified = poly.simplify(t, preserve_topology=True)
        for _ in range(8):
            n = len(simplified.exterior.coords)
            if n <= max_vertices:
                break
            t *= 1.5
            simplified = poly.simplify(t, preserve_topology=True)
        return simplified

    if geom.geom_type == "Polygon":
        return _simplify_poly(geom)
    if geom.geom_type == "MultiPolygon":
        return MultiPolygon([_simplify_poly(p) for p in geom.geoms])
    return geom.simplify(tolerance, preserve_topology=True)


def polygonize_zones(
    zone_int: np.ndarray,
    h: np.ndarray,
    profile: dict,
    district: gpd.GeoDataFrame,
    ls_provenance: str,
) -> gpd.GeoDataFrame:
    features = []
    for geom_dict, val in shapes(zone_int, mask=zone_int > 0, transform=profile["transform"]):
        zone_class = INT_TO_ZONE_CLASS.get(int(val))
        if zone_class is None:
            continue
        geom = shape(geom_dict)
        if geom.is_empty:
            continue
        cell_mask = geometry_mask(
            [geom], out_shape=h.shape, transform=profile["transform"], invert=True
        )
        vals = h[cell_mask]
        vals = vals[~np.isnan(vals)]
        features.append(
            {
                "zone_class": zone_class,
                "geometry": geom,
                "h_mean": round(float(np.mean(vals)), 4) if len(vals) else 0.0,
                "h_max": round(float(np.max(vals)), 4) if len(vals) else 0.0,
                "source": "DERIVED",
            }
        )

    if not features:
        return gpd.GeoDataFrame(
            columns=["zone_class", "h_mean", "h_max", "source", "area_ha", "geometry"],
            crs=DISPLAY_CRS,
        )

    gdf = gpd.GeoDataFrame(features, crs=COMPUTE_CRS)
    gdf = gdf.dissolve(
        by="zone_class", aggfunc={"h_mean": "mean", "h_max": "max", "source": "first"}
    ).reset_index()

    gdf["geometry"] = gdf.geometry.apply(simplify_geometry)
    gdf["area_ha"] = gdf.geometry.area / 10000.0
    gdf = gdf[gdf["area_ha"] >= MIN_ZONE_AREA_HA].copy()

    district_utm = to_compute(district)
    boundary = unary_union(district_utm.geometry)
    gdf["geometry"] = gdf.geometry.intersection(boundary)
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf["area_ha"] = gdf.geometry.area / 10000.0

    if ls_provenance == "DERIVED":
        gdf["source"] = "DERIVED"
    return to_display(gdf)


def compute_hazard_grid_fallback(weights: dict, district: gpd.GeoDataFrame, landslides: gpd.GeoDataFrame):
    """Grid fallback when rasterio or processed rasters are unavailable."""
    from shapely.geometry import box

    bounds = district.total_bounds
    grid_size = 40
    lon_bins = np.linspace(bounds[0], bounds[2], grid_size)
    lat_bins = np.linspace(bounds[1], bounds[3], grid_size)
    yy, xx = np.mgrid[0 : grid_size - 1, 0 : grid_size - 1]
    slope_proxy = normalize_0_1(xx / (grid_size - 1) * 0.5 + yy / (grid_size - 1) * 0.5)
    rainfall_proxy = np.full_like(slope_proxy, 0.5)
    wetness_proxy = normalize_0_1(1 - xx / (grid_size - 1))
    kde = np.zeros_like(slope_proxy)
    if len(landslides) > 0:
        for _, row in landslides.iterrows():
            lon, lat = row.geometry.x, row.geometry.y
            xi = np.searchsorted(lon_bins, lon) - 1
            yi = np.searchsorted(lat_bins, lat) - 1
            if 0 <= xi < grid_size - 1 and 0 <= yi < grid_size - 1:
                kde[yi, xi] += 1
    kde = normalize_0_1(kde)

    h_grid = np.zeros_like(slope_proxy)
    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            h_ls = compute_h_ls(float(slope_proxy[i, j]), float(kde[i, j]), float(rainfall_proxy[i, j]), weights)
            h_ff = compute_h_ff(float(wetness_proxy[i, j]), float(rainfall_proxy[i, j]), weights)
            h_grid[i, j] = compute_multi_hazard(h_ls, h_ff)

    features = []
    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            h_val = float(h_grid[i, j])
            zone = classify_zone(h_val, weights)
            if zone == "Green":
                continue
            poly = box(lon_bins[j], lat_bins[i], lon_bins[j + 1], lat_bins[i + 1])
            features.append(
                {
                    "zone_class": zone,
                    "h_mean": round(h_val, 4),
                    "h_max": round(h_val, 4),
                    "source": "DERIVED",
                    "geometry": poly,
                }
            )
    if not features:
        return gpd.GeoDataFrame(columns=["zone_class", "h_mean", "h_max", "source", "area_ha"], crs=DISPLAY_CRS)
    gdf = gpd.GeoDataFrame(features, crs=DISPLAY_CRS)
    dissolved = gdf.dissolve(by="zone_class", aggfunc={"h_mean": "mean", "h_max": "max", "source": "first"})
    dissolved = dissolved.reset_index()
    dissolved["area_ha"] = dissolved.to_crs(COMPUTE_CRS).geometry.area / 10000
    return dissolved


def main() -> None:
    weights = load_weights()
    paths = load_paths()

    district = gpd.read_file(REPO_ROOT / paths["out"]["district"])
    if district.crs is None:
        district = district.set_crs(DISPLAY_CRS)

    print("Loading landslides...")
    landslides, ls_provenance = load_landslides(paths, district)
    print(f"  {len(landslides)} landslide points ({ls_provenance})")

    slope_path = REPO_ROOT / paths["processed"]["slope"]
    twi_path = REPO_ROOT / paths["processed"]["twi"]
    stream_dist_path = REPO_ROOT / paths["processed"]["stream_dist"]
    hazard_path = REPO_ROOT / paths["processed"]["hazard_raster"]
    dem_path = REPO_ROOT / paths["processed"]["dem_clipped"]

    if HAS_RASTERIO and slope_path.exists() and dem_path.exists():
        print("Computing hazard rasters...")
        with rasterio.open(dem_path) as src:
            profile = src.profile.copy()
            mask_arr = geometry_mask(
                [g for g in to_compute(district).geometry if g is not None],
                out_shape=(src.height, src.width),
                transform=src.transform,
                invert=True,
            )

        slope_deg, _ = read_masked_raster(slope_path, mask_arr)
        twi, _ = read_masked_raster(twi_path, mask_arr) if twi_path.exists() else (np.zeros_like(slope_deg), profile)
        dist_m, _ = (
            read_masked_raster(stream_dist_path, mask_arr)
            if stream_dist_path.exists()
            else (np.full_like(slope_deg, STREAM_PROX_CAP_M), profile)
        )

        landslide_kde, kde_prov = kde_landslide_raster(landslides, profile, mask_arr, slope_deg)
        if kde_prov == "DERIVED":
            ls_provenance = "DERIVED"

        rainfall, has_rainfall = load_rainfall_raster(paths, profile, mask_arr)
        stream_prox = stream_proximity_score(dist_m)
        wetness = wetness_signal(stream_prox, twi)

        h_ls, h_ff, h = compute_hazard_arrays(
            slope_deg, landslide_kde, rainfall, wetness, weights, has_rainfall, mask_arr
        )

        assert np.nanmin(h) >= 0 and np.nanmax(h) <= 1, "Hazard scores out of [0,1]"

        print("Writing hazard rasters...")
        write_hazard_raster(REPO_ROOT / paths["processed"]["h_ls"], h_ls, profile)
        write_hazard_raster(REPO_ROOT / paths["processed"]["h_ff"], h_ff, profile)
        write_hazard_raster(hazard_path, h, profile)

        print("Polygonizing red zones...")
        zone_int = classify_raster(h, weights, mask_arr)
        red_zones = polygonize_zones(zone_int, h, profile, district, ls_provenance)
    else:
        print("  [warn] Processed rasters missing — using grid fallback")
        red_zones = compute_hazard_grid_fallback(weights, district, landslides)

    out_path = REPO_ROOT / paths["out"]["red_zones"]
    red_zones.to_file(out_path, driver="GeoJSON")
    print(f"  Wrote {len(red_zones)} zone polygons to {out_path}")
    print("02_risk_engine.py complete.")


if __name__ == "__main__":
    main()
