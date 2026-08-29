"""Experimental Phase 2D endpoints — gated behind feature flags."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import yaml
from fastapi import APIRouter, HTTPException

REPO_ROOT = Path(__file__).resolve().parents[3]

router = APIRouter()


def _load_features() -> dict:
    path = REPO_ROOT / "config" / "features.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


@router.get("/experimental/weather")
async def live_weather_overlay(lat: float = 30.29, lon: float = 78.98) -> dict:
    features = _load_features()
    if not features.get("live_weather_overlay", False):
        return {
            "enabled": False,
            "experimental": True,
            "note": "Live weather overlay is disabled. Set live_weather_overlay: true in config/features.yaml",
        }
    url = features.get("open_meteo_url", "https://api.open-meteo.com/v1/forecast")
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "precipitation,rain,weather_code",
        "timezone": "Asia/Kolkata",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        return {"enabled": True, "experimental": True, "location": {"lat": lat, "lon": lon}, "data": data}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather API unavailable: {e}")


@router.get("/experimental/districts")
def list_districts() -> dict:
    features = _load_features()
    if not features.get("district_parameterization", False):
        return {
            "enabled": False,
            "experimental": True,
            "districts": [{"id": features.get("default_district_id", "Rudraprayag"), "active": True}],
            "note": "Multi-district parameterization is experimental and disabled by default",
        }
    paths_file = REPO_ROOT / "config" / "paths.yaml"
    paths = yaml.safe_load(paths_file.read_text(encoding="utf-8")) if paths_file.exists() else {}
    return {
        "enabled": True,
        "experimental": True,
        "districts": [{"id": paths.get("district", "Rudraprayag"), "code": paths.get("district_code", "UT_RUD")}],
    }
