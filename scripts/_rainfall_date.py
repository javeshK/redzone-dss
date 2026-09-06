"""Rainfall layers for a specific date — IMD historical or Open-Meteo forecast."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import numpy as np

from _config import REPO_ROOT, load_paths
from _imd_rainfall import IMD_NODATA, _rain_dataarray
from download_data import _effective_bbox

IST = timezone(timedelta(hours=5, minutes=30))

Rudraprayag_CENTER = (30.4, 79.0)  # lat, lon
IMD_MIN_YEAR = 1951
IMD_MAX_YEAR = 2023
FORECAST_MAX_DAYS = 16

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

RainfallMode = Literal["baseline", "historical", "forecast"]


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _http_json(url: str, timeout: int = 30) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RedZone-DSS/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_open_meteo_precip_mm(
    target: date,
    lat: float = Rudraprayag_CENTER[0],
    lon: float = Rudraprayag_CENTER[1],
    *,
    forecast: bool,
) -> float | None:
    """Daily precipitation sum (mm) for one date at district center."""
    ds = target.isoformat()
    base = OPEN_METEO_FORECAST if forecast else OPEN_METEO_ARCHIVE
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "start_date": ds,
        "end_date": ds,
        "timezone": "Asia/Kolkata",
    })
    data = _http_json(f"{base}?{params}")
    if not data:
        return None
    daily = data.get("daily", {})
    times = daily.get("time", [])
    values = daily.get("precipitation_sum", [])
    if not times or not values:
        return None
    for t, v in zip(times, values):
        if t == ds and v is not None:
            return float(v)
    return None


def load_imd_daily_rainfall_mm(
    target: date,
    bbox: tuple[float, float, float, float],
    imd_cache_dir: Path,
) -> np.ndarray | None:
    """IMD gridded daily rainfall (mm) clipped to bbox. Shape (lat, lon)."""
    try:
        import imdlib as imd
    except ImportError:
        return None

    year = target.year
    if year < IMD_MIN_YEAR or year > IMD_MAX_YEAR:
        return None

    min_lon, min_lat, max_lon, max_lat = bbox
    imd_cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        imd.get_data("rain", year, year, fn_format="yearwise", file_dir=str(imd_cache_dir))
        data = imd.open_data("rain", year, year, "yearwise", str(imd_cache_dir))
        da = _rain_dataarray(data.get_xarray())
        da = da.where(da > IMD_NODATA)
        day = da.sel(time=np.datetime64(target.isoformat()), method="nearest")
        if day.sizes.get("time", 1) > 1:
            day = day.isel(time=0)
        layer = day.squeeze(drop=True)
        layer = layer.sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))
        if layer.sizes.get("lat", 0) == 0 or layer.sizes.get("lon", 0) == 0:
            return None
        return layer.values.astype("float32")
    except Exception:
        return None


def mm_to_severity(mm: float, *, cap_mm: float = 150.0) -> float:
    """Map daily mm to 0–1 severity for hazard model."""
    return float(np.clip(mm / cap_mm, 0.0, 1.0))


def build_rainfall_grid_for_date(
    target: date,
    mode: RainfallMode,
    dem_shape: tuple[int, int],
    mask_arr: np.ndarray,
    baseline_rain: np.ndarray,
    paths: dict | None = None,
) -> tuple[np.ndarray, dict]:
    """
    Build normalized 0–1 rainfall grid for scenario scoring.

    Returns (rainfall_grid, metadata).
    """
    paths = paths or load_paths()
    bbox = _effective_bbox(paths)
    imd_cache = REPO_ROOT / paths["raw_dir"] / "imd"
    meta: dict = {
        "date": target.isoformat(),
        "mode": mode,
        "source": "baseline",
        "precip_mm": None,
    }

    if mode == "baseline":
        rain = np.array(baseline_rain, copy=True)
        meta["source"] = "pipeline_rainfall.tif"
        return rain, meta

    if mode == "historical":
        imd_grid = load_imd_daily_rainfall_mm(target, bbox, imd_cache)
        if imd_grid is not None and np.nanmax(imd_grid) > 0:
            mm = float(np.nanmean(imd_grid))
            meta.update({"source": "IMD/imdlib", "precip_mm": round(mm, 2)})
            severity = mm_to_severity(mm)
            # Spatially uniform at IMD cell resolution reprojected via baseline pattern
            base = np.nan_to_num(baseline_rain, nan=0.5)
            base_norm = base / max(np.nanmax(base), 1e-6)
            rain = np.clip(base_norm * severity, 0.0, 1.0)
            rain[~mask_arr] = np.nan
            return rain, meta
        # Fallback: Open-Meteo archive for dates outside IMD
        mm = fetch_open_meteo_precip_mm(target, forecast=False)
        if mm is None:
            raise ValueError(f"No historical rainfall for {target.isoformat()}")
        meta.update({"source": "Open-Meteo/archive", "precip_mm": round(mm, 2)})
        severity = mm_to_severity(mm)
        rain = np.where(mask_arr, severity, np.nan)
        return rain.astype("float32"), meta

    if mode == "forecast":
        today = datetime.now(IST).date()
        if target < today:
            raise ValueError("Forecast mode requires today or a future date")
        if (target - today).days > FORECAST_MAX_DAYS:
            raise ValueError(f"Forecast limited to {FORECAST_MAX_DAYS} days ahead")
        mm = fetch_open_meteo_precip_mm(target, forecast=True)
        if mm is None:
            raise ValueError(f"No forecast rainfall for {target.isoformat()}")
        meta.update({"source": "Open-Meteo/forecast", "precip_mm": round(mm, 2)})
        severity = mm_to_severity(mm)
        rain = np.where(mask_arr, severity, np.nan)
        return rain.astype("float32"), meta

    raise ValueError(f"Unknown mode: {mode}")
