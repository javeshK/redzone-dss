#!/usr/bin/env python3
"""Capture JSON snapshots of key API responses for demo backup / screenshots."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = REPO_ROOT / "docs" / "demo_snapshots"
IST = timezone(timedelta(hours=5, minutes=30))

ENDPOINTS = [
    ("/api/health", "health.json"),
    ("/api/district", "district.json"),
    ("/api/habitations", "habitations.json"),
    ("/api/habitations/UT_RUD_0001", "habitation_ukhimath.json"),
    ("/api/sites", "sites.json"),
    ("/api/recommend/UT_RUD_0001", "recommend_ukhimath.json"),
    ("/api/layers/red_zones", "layer_red_zones.json"),
]


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from fastapi.testclient import TestClient
    from app.main import app

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    meta = {
        "captured_at": datetime.now(IST).isoformat(),
        "endpoints": [],
    }

    print(f"Capturing API snapshots -> {SNAPSHOT_DIR}")
    for path, fname in ENDPOINTS:
        r = client.get(path)
        if r.status_code != 200:
            print(f"  FAILED {path}: HTTP {r.status_code}")
            return 1
        out = SNAPSHOT_DIR / fname
        payload = r.json()
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        meta["endpoints"].append({"path": path, "file": fname, "status": r.status_code})
        print(f"  OK {path} -> {fname}")

    (SNAPSHOT_DIR / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Snapshot capture complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
