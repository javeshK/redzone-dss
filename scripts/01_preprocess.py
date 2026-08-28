#!/usr/bin/env python3
"""01_preprocess.py — Clip, reproject, derive slope/TWI/stream distance."""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from scipy import ndimage
from shapely.geometry import LineString, MultiLineString, box

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, ensure_dirs, load_paths
from _crs import COMPUTE_CRS, DISPLAY_CRS, normalize_0_1, to_compute, to_display, validate_utm_geometry

try:
    import rasterio
    from rasterio.features import geometry_mask, rasterize, shapes
    from rasterio.mask import mask as rio_mask
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


def load_district(paths: dict) -> gpd.GeoDataFrame:
    district_path = REPO_ROOT / paths["raw"]["district"]
    if district_path.exists():
        gdf = gpd.read_file(district_path)
        if gdf.crs is None:
            gdf = gdf.set_crs(DISPLAY_CRS)
        return to_display(gdf)
    bbox = paths["bbox"]
    geom = box(bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"])
    return gpd.GeoDataFrame(
        [{"name": "Rudraprayag", "state": "Uttarakhand", "district_code": "UT_RUD"}],
        geometry=[geom],
        crs=DISPLAY_CRS,
    )


def create_synthetic_dem(district: gpd.GeoDataFrame, out_path: Path, res: float = 90.0) -> Path:
    """Create a synthetic DEM when real tiles are unavailable."""
    from rasterio.transform import from_bounds

    bounds = district.to_crs(COMPUTE_CRS).total_bounds
    width = max(int((bounds[2] - bounds[0]) / res), 10)
    height = max(int((bounds[3] - bounds[1]) / res), 10)
    transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], width, height)
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    xx, yy = np.meshgrid(x, y)
    dem = 2000 + 1500 * (xx * 0.6 + yy * 0.4) + 200 * np.sin(xx * 8) * np.cos(yy * 6)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs=COMPUTE_CRS,
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(dem.astype("float32"), 1)
    return out_path


def reproject_raster(src_path: Path, dst_path: Path, dst_crs: str = COMPUTE_CRS) -> None:
    with rasterio.open(src_path) as src:
        if src.crs and src.crs.to_string() == dst_crs:
            if src_path != dst_path:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy(src_path, dst_path)
            return
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update(
            crs=dst_crs,
            transform=transform,
            width=width,
            height=height,
            dtype="float32",
            nodata=-9999,
        )
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(dst_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear,
                )


def clip_dem_to_district(
    dem_path: Path, district: gpd.GeoDataFrame, out_path: Path
) -> dict:
    """Clip DEM to district boundary in compute CRS; return raster profile dict."""
    district_utm = to_compute(district)
    with rasterio.open(dem_path) as src:
        if src.crs and src.crs.to_string() != COMPUTE_CRS:
            tmp = out_path.parent / "_dem_reproject.tif"
            reproject_raster(dem_path, tmp, COMPUTE_CRS)
            dem_path = tmp
        with rasterio.open(dem_path) as src_utm:
            geoms = [g for g in district_utm.geometry if g is not None]
            out_image, out_transform = rio_mask(src_utm, geoms, crop=True, nodata=-9999)
            dem = out_image[0].astype("float32")
            dem[dem == -9999] = np.nan
            profile = src_utm.profile.copy()
            profile.update(
                height=dem.shape[0],
                width=dem.shape[1],
                transform=out_transform,
                crs=COMPUTE_CRS,
                dtype="float32",
                count=1,
                nodata=-9999,
            )
            out_path.parent.mkdir(parents=True, exist_ok=True)
            write_arr = np.where(np.isnan(dem), -9999, dem).astype("float32")
            with rasterio.open(out_path, "w", **profile) as dst:
                dst.write(write_arr, 1)
    return profile


def district_mask(district: gpd.GeoDataFrame, profile: dict) -> np.ndarray:
    district_utm = to_compute(district)
    geoms = [g for g in district_utm.geometry if g is not None]
    mask = geometry_mask(
        geoms,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        invert=True,
    )
    return mask


def compute_slope(dem_path: Path, slope_path: Path, district_mask_arr: np.ndarray | None = None) -> None:
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(float)
        dem[dem == src.nodata] = np.nan
        transform = src.transform
        res_x = abs(transform.a)
        res_y = abs(transform.e)
        dy, dx = np.gradient(np.nan_to_num(dem, nan=np.nanmean(dem)), res_y, res_x)
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_deg = np.degrees(slope_rad)
        if district_mask_arr is not None:
            slope_deg = np.where(district_mask_arr, slope_deg, np.nan)
        profile = src.profile.copy()
        profile.update(dtype="float32", count=1, nodata=-9999)
        slope_path.parent.mkdir(parents=True, exist_ok=True)
        out = np.where(np.isnan(slope_deg), -9999, slope_deg).astype("float32")
        with rasterio.open(slope_path, "w", **profile) as dst:
            dst.write(out, 1)


def compute_twi(dem_path: Path, slope_path: Path, twi_path: Path, district_mask_arr: np.ndarray) -> None:
    """TWI proxy from specific catchment area and slope (DEM-derived)."""
    with rasterio.open(dem_path) as dem_src, rasterio.open(slope_path) as slope_src:
        dem = dem_src.read(1).astype(float)
        dem[dem == dem_src.nodata] = np.nan
        slope_deg = slope_src.read(1).astype(float)
        slope_deg[slope_deg == slope_src.nodata] = np.nan
        res = abs(dem_src.transform.a)
        slope_rad = np.radians(np.clip(slope_deg, 0.1, 89.9))
        dy, dx = np.gradient(np.nan_to_num(dem, nan=np.nanmean(dem)), res, res)
        grad_mag = np.sqrt(dx**2 + dy**2) + 1e-6
        sca = res / grad_mag
        twi = np.log(np.maximum(sca, 1.0) / np.tan(slope_rad) + 1e-6)
        twi = np.where(district_mask_arr, twi, np.nan)
        profile = dem_src.profile.copy()
        profile.update(dtype="float32", count=1, nodata=-9999)
        twi_path.parent.mkdir(parents=True, exist_ok=True)
        out = np.where(np.isnan(twi), -9999, twi).astype("float32")
        with rasterio.open(twi_path, "w", **profile) as dst:
            dst.write(out, 1)


def load_or_derive_streams(
    paths: dict, district: gpd.GeoDataFrame, twi_path: Path | None, profile: dict | None
) -> gpd.GeoDataFrame:
    streams_raw = REPO_ROOT / paths["raw"]["osm_waterways"]
    out_path = REPO_ROOT / paths["out"]["streams"]
    if streams_raw.exists():
        gdf = gpd.read_file(streams_raw)
        if gdf.crs is None:
            gdf = gdf.set_crs(DISPLAY_CRS)
        gdf = gpd.clip(gdf, district)
        if len(gdf) > 0:
            gdf["source"] = "OPEN_DATA"
            gdf.to_file(out_path, driver="GeoJSON")
            return gdf

    if twi_path and twi_path.exists() and profile and HAS_RASTERIO:
        print("  [warn] No OSM waterways — deriving stream paths from TWI (DERIVED)")
        with rasterio.open(twi_path) as src:
            twi = src.read(1).astype(float)
            twi[twi == src.nodata] = np.nan
            valid = twi[~np.isnan(twi)]
            if len(valid) > 0:
                threshold = float(np.nanpercentile(valid, 92))
                stream_mask = twi >= threshold
                lines = []
                for geom, val in shapes(stream_mask.astype(np.uint8), mask=stream_mask, transform=src.transform):
                    if val != 1:
                        continue
                    coords = geom["coordinates"]
                    if geom["type"] == "LineString":
                        lines.append(LineString(coords))
                    elif geom["type"] == "MultiLineString":
                        lines.extend(LineString(part) for part in coords)
                if lines:
                    merged = MultiLineString(lines)
                    gdf = gpd.GeoDataFrame(
                        [{"name": "derived_stream", "source": "DERIVED"}],
                        geometry=[merged],
                        crs=COMPUTE_CRS,
                    )
                    gdf = to_display(gdf)
                    gdf.to_file(out_path, driver="GeoJSON")
                    return gdf

    if out_path.exists():
        return gpd.read_file(out_path)
    print("  [warn] No streams available — flash-flood wetness will use TWI only")
    return gpd.GeoDataFrame(geometry=[], crs=DISPLAY_CRS)


def compute_stream_distance(
    streams: gpd.GeoDataFrame,
    profile: dict,
    district_mask_arr: np.ndarray,
    out_path: Path,
) -> None:
    """Distance to nearest stream in meters (capped at 1000 m for wetness scoring)."""
    stream_raster = np.zeros((profile["height"], profile["width"]), dtype=np.uint8)
    if len(streams) > 0:
        streams_utm = to_compute(streams)
        shapes_gen = ((geom, 1) for geom in streams_utm.geometry if geom is not None)
        stream_raster = rasterize(
            shapes_gen,
            out_shape=(profile["height"], profile["width"]),
            transform=profile["transform"],
            fill=0,
            dtype=np.uint8,
        )
    dist_m = ndimage.distance_transform_edt(stream_raster == 0, sampling=(abs(profile["transform"].e), abs(profile["transform"].a)))
    dist_m = np.where(district_mask_arr, dist_m, np.nan)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = np.where(np.isnan(dist_m), -9999, dist_m).astype("float32")
    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=profile["height"],
        width=profile["width"],
        count=1,
        dtype="float32",
        crs=profile["crs"],
        transform=profile["transform"],
        nodata=-9999,
    ) as dst:
        dst.write(out, 1)


def main() -> None:
    paths = load_paths()
    ensure_dirs(
        REPO_ROOT / paths["raw_dir"],
        REPO_ROOT / paths["processed_dir"],
        REPO_ROOT / paths["out_dir"],
    )

    print("Loading district boundary...")
    district = load_district(paths)
    validate_utm_geometry(district, "district")

    district_out = REPO_ROOT / paths["out"]["district"]
    district.to_file(district_out, driver="GeoJSON")
    print(f"  Wrote {district_out}")

    dem_clipped = REPO_ROOT / paths["processed"]["dem_clipped"]
    slope_path = REPO_ROOT / paths["processed"]["slope"]
    twi_path = REPO_ROOT / paths["processed"]["twi"]
    stream_dist_path = REPO_ROOT / paths["processed"]["stream_dist"]

    if not HAS_RASTERIO:
        print("  [warn] rasterio not available — skipping DEM/slope/TWI")
        export_streams(paths, district)
        print("01_preprocess.py complete.")
        return

    raw_dem_dir = REPO_ROOT / paths["raw"]["dem"]
    dem_files = list(raw_dem_dir.glob("*.tif")) if raw_dem_dir.exists() else []
    if dem_files:
        print(f"Clipping DEM: {dem_files[0].name}")
        profile = clip_dem_to_district(dem_files[0], district, dem_clipped)
    else:
        print("  [warn] No DEM found — generating synthetic DEM (SYNTHETIC)")
        synthetic = dem_clipped.parent / "_synthetic_dem.tif"
        create_synthetic_dem(district, synthetic)
        profile = clip_dem_to_district(synthetic, district, dem_clipped)

    mask_arr = district_mask(district, profile)

    print("Computing slope...")
    compute_slope(dem_clipped, slope_path, mask_arr)
    print(f"  Wrote {slope_path}")

    print("Computing TWI...")
    compute_twi(dem_clipped, slope_path, twi_path, mask_arr)
    print(f"  Wrote {twi_path}")

    print("Exporting streams...")
    streams = load_or_derive_streams(paths, district, twi_path, profile)
    print(f"  {len(streams)} stream features")

    print("Computing stream distance raster...")
    compute_stream_distance(streams, profile, mask_arr, stream_dist_path)
    print(f"  Wrote {stream_dist_path}")

    print("01_preprocess.py complete.")


def export_streams(paths: dict, district: gpd.GeoDataFrame) -> None:
    """Legacy helper when rasterio is unavailable."""
    streams_raw = REPO_ROOT / paths["raw"]["osm_waterways"]
    out_path = REPO_ROOT / paths["out"]["streams"]
    if streams_raw.exists():
        gdf = gpd.read_file(streams_raw)
        if gdf.crs is None:
            gdf = gdf.set_crs(DISPLAY_CRS)
        gdf = gpd.clip(gdf, district)
        gdf.to_file(out_path, driver="GeoJSON")


if __name__ == "__main__":
    main()
