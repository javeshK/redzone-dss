#!/usr/bin/env python3
"""05_export.py — Write meta.json, copy out/ to frontend/public/data/."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths, load_weights
from _crs import COMPUTE_CRS

IST = timezone(timedelta(hours=5, minutes=30))


def _detect_degraded_mode(paths: dict) -> bool:
    rainfall = REPO_ROOT / paths["raw"]["rainfall"]
    return not rainfall.exists()


def _detect_synthetic_mode(paths: dict) -> bool:
    dem_dir = REPO_ROOT / paths["raw"]["dem"]
    dem_files = list(dem_dir.glob("*.tif")) if dem_dir.exists() else []
    return len(dem_files) == 0


def _layer_provenance(layer: str, paths: dict) -> str:
    if layer == "streams":
        raw = REPO_ROOT / paths["raw"]["osm_waterways"]
        if raw.exists():
            return "OPEN_DATA"
        out = REPO_ROOT / paths["out"]["streams"]
        if out.exists():
            try:
                data = json.loads(out.read_text(encoding="utf-8"))
                return data["features"][0]["properties"].get("source", "DERIVED")
            except (IndexError, KeyError, json.JSONDecodeError):
                pass
        return "DERIVED"
    if layer == "landslides":
        raw = REPO_ROOT / paths["raw"]["landslides"]
        return "OPEN_DATA" if raw.exists() else "DERIVED"
    if layer == "red_zones":
        return "DERIVED"
    if layer == "habitations":
        return "EXPERT_SCREENED"
    if layer == "sites":
        return "EXPERT_SCREENED"
    return "OPEN_DATA"


def build_meta(weights: dict, paths: dict) -> dict:
    hab_path = REPO_ROOT / paths["out"]["habitations"]
    sites_path = REPO_ROOT / paths["out"]["sites"]
    rz_path = REPO_ROOT / paths["out"]["red_zones"]
    district_path = REPO_ROOT / paths["out"]["district"]

    habs = json.loads(hab_path.read_text(encoding="utf-8")) if hab_path.exists() else {"features": []}
    sites = json.loads(sites_path.read_text(encoding="utf-8")) if sites_path.exists() else {"features": []}

    priority_counts = {"Immediate": 0, "Short-term": 0, "Medium-term": 0, "Monitor": 0}
    for f in habs["features"]:
        p = f["properties"].get("priority", "Monitor")
        if p in priority_counts:
            priority_counts[p] += 1

    red_orange_yellow_area = 0.0
    district_area_ha = 198000.0
    if rz_path.exists():
        try:
            import geopandas as gpd
            rz = gpd.read_file(rz_path)
            if "area_ha" in rz.columns:
                red_orange_yellow_area = float(rz["area_ha"].sum())
            else:
                rz_utm = rz.to_crs(COMPUTE_CRS)
                red_orange_yellow_area = rz_utm.geometry.area.sum() / 10000
        except Exception:
            red_orange_yellow_area = 0.0

    if district_path.exists():
        try:
            import geopandas as gpd
            district = gpd.read_file(district_path).to_crs(COMPUTE_CRS)
            district_area_ha = round(district.geometry.area.sum() / 10000, 1)
        except Exception:
            pass

    degraded = _detect_degraded_mode(paths)
    synthetic = _detect_synthetic_mode(paths)

    sources = [
        {"layer": "district", "provenance": "OPEN_DATA", "url": "https://github.com/datameet/maps",
         "note": "Rudraprayag district boundary"},
        {"layer": "habitations", "provenance": _layer_provenance("habitations", paths), "url": None,
         "note": "Demo subset with hazard scores sampled from pipeline rasters where available"},
        {"layer": "red_zones", "provenance": "DERIVED", "url": None,
         "note": "Multi-criteria hazard model output — not official government zonation"},
        {"layer": "landslides", "provenance": _layer_provenance("landslides", paths),
         "url": "https://bharatlas.com/view/gsi_landslide_inventory",
         "note": "GSI inventory clipped to district or slope proxy"},
        {"layer": "streams", "provenance": _layer_provenance("streams", paths),
         "url": "https://download.geofabrik.de/",
         "note": "OSM waterways or TWI-derived stream paths"},
        {"layer": "sites", "provenance": "EXPERT_SCREENED", "url": None,
         "note": "Candidate relocation sites screened by hazard, slope, and buildability"},
    ]
    if synthetic:
        sources.append({"layer": "dem", "provenance": "SYNTHETIC", "url": None,
                        "note": "Synthetic DEM used when Copernicus/SRTM tiles unavailable"})
    if degraded:
        sources.append({"layer": "rainfall", "provenance": "SYNTHETIC", "url": None,
                        "note": "Uniform rainfall proxy; hazard weights renormalized"})

    return {
        "district": paths["district"],
        "generated_at": datetime.now(IST).isoformat(),
        "model_version": weights["model_version"],
        "weights_version": weights["weights_version"],
        "degraded_mode": degraded,
        "synthetic_data_used": synthetic or degraded,
        "sources": sources,
        "limitations": [
            "Derived hazard scores are decision-support indicators, not official government hazard zonation.",
            "Carrying capacity is first-order physical screening capacity, not statutory or legally approved settlement capacity.",
            "Demo dataset uses a curated subset of habitations; synthetic enrichment is flagged where applied.",
            "Rainfall and vulnerability proxies may use fallback values when primary sources are unavailable.",
        ],
        "kpis": {
            "habitation_count": len(habs["features"]),
            "immediate_count": priority_counts["Immediate"],
            "short_term_count": priority_counts["Short-term"],
            "medium_term_count": priority_counts["Medium-term"],
            "monitor_count": priority_counts["Monitor"],
            "site_count": len(sites["features"]),
            "red_zone_area_ha": round(red_orange_yellow_area, 1),
            "district_area_ha": district_area_ha,
        },
    }


def copy_to_public(paths: dict) -> list[Path]:
    out_dir = REPO_ROOT / paths["out_dir"]
    public_dir = REPO_ROOT / paths["public_data_dir"]
    public_dir.mkdir(parents=True, exist_ok=True)

    files = [
        "district.geojson", "habitations.geojson", "red_zones.geojson",
        "sites.geojson", "landslides.geojson", "streams.geojson",
        "meta.json", "recommendations.json",
    ]
    copied: list[Path] = []
    for fname in files:
        src = out_dir / fname
        if src.exists():
            dest = public_dir / fname
            shutil.copy2(src, dest)
            copied.append(dest)
            print(f"  Copied {fname} -> {dest}")
    return copied


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_export_manifest(paths: dict, copied: list[Path]) -> dict:
    out_dir = REPO_ROOT / paths["out_dir"]
    public_dir = REPO_ROOT / paths["public_data_dir"]
    entries = []
    for path in sorted(copied, key=lambda p: p.name):
        src = out_dir / path.name
        entries.append({
            "file": path.name,
            "out_bytes": src.stat().st_size if src.exists() else 0,
            "public_bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "in_sync": src.exists() and src.stat().st_size == path.stat().st_size,
        })
    return {
        "generated_at": datetime.now(IST).isoformat(),
        "out_dir": str(out_dir.relative_to(REPO_ROOT)),
        "public_data_dir": str(public_dir.relative_to(REPO_ROOT)),
        "files": entries,
        "parity_ok": all(e["in_sync"] for e in entries),
    }


def copy_to_dist(paths: dict, copied: list[Path]) -> None:
    dist_dir = REPO_ROOT / "frontend" / "dist" / "data"
    if not (REPO_ROOT / "frontend" / "dist").exists():
        return
    dist_dir.mkdir(parents=True, exist_ok=True)
    for path in copied:
        shutil.copy2(path, dist_dir / path.name)
    print(f"  Synced {len(copied)} files -> {dist_dir}")


def main():
    weights = load_weights()
    paths = load_paths()

    print("Building meta.json...")
    meta = build_meta(weights, paths)
    meta_path = REPO_ROOT / paths["out"]["meta"]
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  Wrote {meta_path}")

    print("Copying to frontend/public/data/...")
    copied = copy_to_public(paths)

    manifest = build_export_manifest(paths, copied)
    manifest_path = REPO_ROOT / paths["out_dir"] / "export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    shutil.copy2(manifest_path, REPO_ROOT / paths["public_data_dir"] / "export_manifest.json")
    print(f"  Wrote {manifest_path} (parity_ok={manifest['parity_ok']})")

    copy_to_dist(paths, copied)
    print("05_export.py complete.")


if __name__ == "__main__":
    main()
