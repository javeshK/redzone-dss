"""Rule-based alerts API."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "out"

router = APIRouter()


@router.get("/alerts")
def list_alerts() -> dict:
    alerts_path = OUT_DIR / "alerts.json"
    if not alerts_path.exists():
        return {"generated_at": None, "alert_count": 0, "alerts": []}
    return json.loads(alerts_path.read_text(encoding="utf-8"))


@router.get("/habitations/{hab_id}/pdf")
def habitation_pdf(hab_id: str):
    pdf_path = OUT_DIR / "pdf" / f"{hab_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found for {hab_id}")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{hab_id}.pdf")
