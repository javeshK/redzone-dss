"""Rainfall scenario slider API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.scenario_service import scenario_service

router = APIRouter()

VALID_MODES = ("baseline", "historical", "forecast")


@router.get("/scenario/rainfall")
def rainfall_scenario(
    factor: float = Query(1.0, description="Rainfall scale factor: 1.0, 1.2, or 1.5"),
    date: str | None = Query(None, description="ISO date YYYY-MM-DD for historical or forecast"),
    mode: str = Query("baseline", description="baseline | historical | forecast"),
) -> dict:
    if factor not in (1.0, 1.2, 1.5):
        raise HTTPException(status_code=400, detail="factor must be 1.0, 1.2, or 1.5")
    if mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"mode must be one of {VALID_MODES}")
    if mode != "baseline" and not date:
        raise HTTPException(status_code=400, detail="date is required when mode is historical or forecast")

    result = scenario_service.get_rainfall_scenario(factor, scenario_date=date, mode=mode)
    if "error" in result:
        err = str(result["error"])
        if "factor must be" in err:
            raise HTTPException(status_code=400, detail=err)
        if "processed rasters unavailable" in err:
            raise HTTPException(status_code=503, detail=err)
        raise HTTPException(status_code=400, detail=err)
    return result
