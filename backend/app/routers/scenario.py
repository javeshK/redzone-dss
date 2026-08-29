"""Rainfall scenario slider API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.scenario_service import scenario_service

router = APIRouter()


@router.get("/scenario/rainfall")
def rainfall_scenario(
    factor: float = Query(1.0, description="Rainfall scale factor: 1.0, 1.2, or 1.5"),
) -> dict:
    if factor not in (1.0, 1.2, 1.5):
        raise HTTPException(status_code=400, detail="factor must be 1.0, 1.2, or 1.5")
    result = scenario_service.get_rainfall_scenario(factor)
    if "error" in result and result["error"] != f"factor must be one of {(1.0, 1.2, 1.5)}":
        if "processed rasters unavailable" in str(result.get("error", "")):
            raise HTTPException(status_code=503, detail=result["error"])
    return result
