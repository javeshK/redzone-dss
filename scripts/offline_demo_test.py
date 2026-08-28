#!/usr/bin/env python3
"""Verify the static/offline demo path without a running API or dev server."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC = REPO_ROOT / "frontend" / "public" / "data"
DIST = REPO_ROOT / "frontend" / "dist" / "data"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_static_bundle(data_dir: Path, label: str) -> list[str]:
    errors: list[str] = []
    required = [
        "district.geojson",
        "habitations.geojson",
        "meta.json",
        "recommendations.json",
        "sites.geojson",
    ]
    for fname in required:
        if not (data_dir / fname).exists():
            errors.append(f"{label}: missing {fname}")

    if errors:
        return errors

    district = _load(data_dir / "district.geojson")
    meta = _load(data_dir / "meta.json")
    habitations = _load(data_dir / "habitations.geojson")
    recs = _load(data_dir / "recommendations.json")
    sites = _load(data_dir / "sites.geojson")

    if not district.get("features"):
        errors.append(f"{label}: district.geojson has no features")
    if len(habitations.get("features", [])) < 25:
        errors.append(f"{label}: expected >= 25 habitations")
    if len(sites.get("features", [])) < 8:
        errors.append(f"{label}: expected >= 8 sites")
    if not meta.get("kpis"):
        errors.append(f"{label}: meta.json missing kpis")

    sample_id = habitations["features"][0]["properties"]["id"]
    if sample_id not in recs.get("recommendations", {}):
        errors.append(f"{label}: no recommendation for sample habitation {sample_id}")

    ukhimath = recs["recommendations"].get("UT_RUD_0001")
    if ukhimath:
        top = ukhimath.get("top", {})
        if not top.get("reasons"):
            errors.append(f"{label}: Ukhimath recommendation missing reasons")
        if not top.get("explain"):
            errors.append(f"{label}: Ukhimath recommendation missing U_ij explain")

    return errors


def main() -> int:
    print("RedZone DSS — Offline Static Demo Test")
    print("=" * 40)
    errors: list[str] = []
    errors += check_static_bundle(PUBLIC, "public/data")
    if DIST.exists():
        errors += check_static_bundle(DIST, "dist/data")
    else:
        print("  [info] frontend/dist/data not found — run npm run build first")

    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASSED: Static bundles are complete for offline preview.")
    print()
    print("Offline demo:")
    print("  cd frontend && npm run build && npm run preview")
    print("  Open http://localhost:4173 (no API required)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
