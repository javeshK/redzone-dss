"""Fetch IMD gridded rainfall via imdlib and export a single-band GeoTIFF for the pipeline."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))

IMD_NODATA = -999.0

# Kedarnath / monsoon demo window (PS26191 spec: June 2013 anomaly)
IMD_RAIN_YEAR = 2013
IMD_RAIN_MONTH_START = "2013-06-01"
IMD_RAIN_MONTH_END = "2013-06-30"


def _rain_dataarray(ds):
    """Extract rainfall DataArray from imdlib xarray Dataset."""
    if hasattr(ds, "data_vars"):
        if "rain" in ds.data_vars:
            return ds["rain"]
        return next(iter(ds.data_vars.values()))
    return ds


def fetch_imd_rainfall_geotiff(
    out_path: Path,
    bbox: tuple[float, float, float, float],
    imd_cache_dir: Path,
    year: int = IMD_RAIN_YEAR,
    month_start: str = IMD_RAIN_MONTH_START,
    month_end: str = IMD_RAIN_MONTH_END,
) -> dict:
    """
    Download IMD daily rainfall for `year`, sum to one monthly layer, clip to bbox.

    Follows: https://pratiman-91.github.io/2020/10/06/IMD-grided-to-GeoTIFF.html
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    entry = {
        "layer": "rainfall",
        "source": "DERIVED_OROGRAPHIC",
        "live": False,
        "path": str(out_path),
    }

    try:
        import imdlib as imd
    except ImportError:
        print("  [warn] imdlib not installed — pip install imdlib rioxarray")
        return entry

    try:
        import rioxarray  # noqa: F401
    except ImportError:
        print("  [warn] rioxarray not installed — pip install rioxarray")
        return entry

    imd_cache_dir.mkdir(parents=True, exist_ok=True)
    variable = "rain"

    print(f"Downloading IMD gridded rainfall for {year} (imdlib)...")
    try:
        imd.get_data(variable, year, year, fn_format="yearwise", file_dir=str(imd_cache_dir))
    except Exception as e:
        print(f"  [warn] IMD download failed: {e}")
        return entry

    try:
        data = imd.open_data(variable, year, year, "yearwise", str(imd_cache_dir))
        da = _rain_dataarray(data.get_xarray())
    except Exception as e:
        print(f"  [warn] IMD open failed: {e}")
        return entry

    if da is None or "time" not in da.dims:
        print("  [warn] IMD xarray missing time dimension")
        return entry

    # Mask IMD nodata (-999) before aggregation
    da = da.where(da > IMD_NODATA)

    monthly = da.sel(time=slice(month_start, month_end))
    if monthly.sizes.get("time", 0) == 0:
        print(f"  [warn] No IMD data for {month_start} to {month_end}")
        return entry

    layer = monthly.sum(dim="time", skipna=True)
    layer = layer.sel(
        lat=slice(min_lat, max_lat),
        lon=slice(min_lon, max_lon),
    )

    if layer.sizes.get("lat", 0) == 0 or layer.sizes.get("lon", 0) == 0:
        print("  [warn] IMD clip produced empty extent")
        return entry

    pr = layer.rio.write_crs("EPSG:4326")
    pr = pr.rio.set_spatial_dims(x_dim="lon", y_dim="lat")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pr.rio.to_raster(str(out_path), driver="GTiff")

    if not out_path.exists() or out_path.stat().st_size < 200:
        print("  [warn] IMD GeoTIFF output too small or missing")
        return entry

    print(
        f"  Saved IMD June {year} rainfall "
        f"({layer.sizes['lat']}x{layer.sizes['lon']} cells) to {out_path}"
    )
    return {
        "layer": "rainfall",
        "source": "IMD/imdlib",
        "live": True,
        "path": str(out_path),
        "period": f"{month_start} to {month_end}",
        "data_as_of": datetime.now(IST).isoformat(),
        "note": "IMD gridded daily rain (0.25 deg) summed to June monthly total; clipped to district bbox",
    }
