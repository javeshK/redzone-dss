#!/usr/bin/env python3
"""Offline demo validation — run before judge presentation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "out"
PUBLIC = REPO_ROOT / "frontend" / "public" / "data"

REQUIRED_FILES = [
    "district.geojson",
    "habitations.geojson",
    "red_zones.geojson",
    "sites.geojson",
    "landslides.geojson",
    "streams.geojson",
    "meta.json",
    "recommendations.json",
    "export_manifest.json",
]


def check_files(directory: Path, label: str) -> list[str]:
    errors = []
    for fname in REQUIRED_FILES:
        path = directory / fname
        if not path.exists():
            errors.append(f"Missing {label}/{fname}")
        elif path.stat().st_size == 0:
            errors.append(f"Empty {label}/{fname}")
    return errors


def check_parity() -> list[str]:
    errors = []
    manifest_path = OUT / "export_manifest.json"
    if not manifest_path.exists():
        return errors
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("parity_ok"):
        errors.append("export_manifest.json reports out/ ↔ public/ parity failure")
    for entry in manifest.get("files", []):
        fname = entry["file"]
        out_path = OUT / fname
        pub_path = PUBLIC / fname
        if out_path.exists() and pub_path.exists():
            if out_path.stat().st_size != pub_path.stat().st_size:
                errors.append(f"Size mismatch for {fname}: out vs public")
    return errors


def check_recommendations(path: Path) -> list[str]:
    errors = []
    data = json.loads(path.read_text(encoding="utf-8"))
    recs = data.get("recommendations", {})
    if not recs:
        errors.append("No recommendations in recommendations.json")
    for hab_id, rec in recs.items():
        top = rec.get("top", {})
        if not top:
            errors.append(f"{hab_id}: missing top recommendation")
        if "reasons" not in top:
            errors.append(f"{hab_id}: missing reasons")
        if "explain" not in top or len(top.get("explain", [])) < 7:
            errors.append(f"{hab_id}: missing or incomplete U_ij explain breakdown")
        if rec.get("runner_up") is None:
            errors.append(f"{hab_id}: missing runner_up")
        if rec.get("comparison") is None:
            errors.append(f"{hab_id}: missing comparison block")
    return errors


def check_meta(meta_path: Path, hab_count: int) -> list[str]:
    errors = []
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not meta.get("limitations"):
        errors.append("meta.json missing limitations")
    kpis = meta.get("kpis", {})
    if kpis.get("habitation_count", 0) < 25:
        errors.append(f"Expected >= 25 habitations in KPIs, got {kpis.get('habitation_count')}")
    if kpis.get("site_count", 0) < 8:
        errors.append(f"Expected >= 8 sites in KPIs, got {kpis.get('site_count')}")
    if meta.get("synthetic_data_used") and not any(
        s.get("provenance") == "SYNTHETIC" for s in meta.get("sources", [])
    ):
        print("  [info] synthetic_data_used=true but no SYNTHETIC source tag (acceptable for demo)")
    return errors


def main() -> int:
    print("RedZone DSS — Offline Demo Validation")
    print("=" * 40)
    errors = []
    errors += check_files(OUT, "out")
    errors += check_files(PUBLIC, "frontend/public/data")
    errors += check_parity()

    rec_path = OUT / "recommendations.json"
    if rec_path.exists():
        errors += check_recommendations(rec_path)

    hab_path = OUT / "habitations.geojson"
    hab_count = 0
    if hab_path.exists():
        hab_count = len(json.loads(hab_path.read_text(encoding="utf-8")).get("features", []))
        if hab_count < 25:
            errors.append(f"Expected >= 25 habitations, got {hab_count}")

    sites_path = OUT / "sites.geojson"
    if sites_path.exists():
        site_count = len(json.loads(sites_path.read_text(encoding="utf-8")).get("features", []))
        if site_count < 8:
            errors.append(f"Expected >= 8 sites, got {site_count}")

    meta_path = OUT / "meta.json"
    if meta_path.exists():
        errors += check_meta(meta_path, hab_count)

    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASSED: All offline demo artifacts present and valid.")
    print()
    print("Demo startup:")
    print("  cd backend && uvicorn app.main:app --port 8000")
    print("  cd frontend && npm run dev")
    print("  OR: cd frontend && npm run build && npm run preview  (fully offline)")
    print()
    print("Pre-demo checklist:")
    print("  python scripts/validate_demo.py")
    print("  cd backend && pytest tests/ -v")
    return 0


if __name__ == "__main__":
    sys.exit(main())
