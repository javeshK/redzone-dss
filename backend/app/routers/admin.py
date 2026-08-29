"""Admin pipeline refresh endpoints."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "out"
IST = timezone(timedelta(hours=5, minutes=30))

router = APIRouter()


def _read_run_log() -> dict:
    log_path = OUT_DIR / "run_log.json"
    if not log_path.exists():
        return {"success": False, "note": "No pipeline run recorded yet"}
    return json.loads(log_path.read_text(encoding="utf-8"))


@router.get("/meta/refresh-status")
def refresh_status() -> dict:
    log = _read_run_log()
    return {
        "last_run": log.get("ended_at") or log.get("started_at"),
        "success": log.get("success", False),
        "duration_s": log.get("duration_s"),
        "pipeline_version": log.get("pipeline_version", "2.0.0"),
        "steps": log.get("steps", []),
    }


@router.post("/admin/refresh")
def trigger_refresh() -> dict:
    api_key = os.environ.get("REDZONE_API_KEY", "dev-local")
    header_key = os.environ.get("REDZONE_REFRESH_ALLOWED", "true")
    if header_key.lower() == "false":
        raise HTTPException(status_code=403, detail="Pipeline refresh disabled in this environment")

    pipeline_script = REPO_ROOT / "scripts" / "07_run_pipeline.py"
    if not pipeline_script.exists():
        raise HTTPException(status_code=500, detail="Pipeline script not found")

    started = datetime.now(IST).isoformat()
    result = subprocess.run(
        [sys.executable, str(pipeline_script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    from app.data_loader import store
    store.load(force=True)

    log = _read_run_log()
    return {
        "triggered_at": started,
        "api_key_hint": f"Set REDZONE_API_KEY env var (current: {api_key[:3]}...)",
        "returncode": result.returncode,
        "success": result.returncode == 0,
        "last_run": log.get("ended_at"),
        "duration_s": log.get("duration_s"),
    }
