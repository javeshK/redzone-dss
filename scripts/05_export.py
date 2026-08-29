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
    """True only when core rasters are missing entirely (not terrain-derived)."""
    dem_dir = REPO_ROOT / paths["raw"]["dem"]
    dem_files = list(dem_dir.glob("*.tif")) if dem_dir.exists() else []
    rainfall = REPO_ROOT / paths["raw"]["rainfall"]
    return len(dem_files) == 0 or not rainfall.exists()


def _file_mtime_iso(path: Path) -> str | None:
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime, IST).isoformat()
    return None


def _layer_data_hash(path: Path) -> str | None:
    if path.exists() and path.is_file():
        return _sha256(path)
    if path.exists() and path.is_dir():
        files = sorted(path.glob("*.tif"))
        if files:
            return _sha256(files[0])
    return None


def _collect_data_layers(paths: dict) -> dict:
    """Per-layer hashes and data_as_of timestamps for audit trail."""
    layer_paths = {
        "district": REPO_ROOT / paths["raw"]["district"],
        "dem": REPO_ROOT / paths["raw"]["dem"],
        "landslides": REPO_ROOT / paths["raw"]["landslides"],
        "rainfall": REPO_ROOT / paths["raw"]["rainfall"],
        "villages": REPO_ROOT / paths["raw"]["villages"],
        "osm_waterways": REPO_ROOT / paths["raw"]["osm_waterways"],
        "habitations": REPO_ROOT / paths["out"]["habitations"],
        "red_zones": REPO_ROOT / paths["out"]["red_zones"],
        "sites": REPO_ROOT / paths["out"]["sites"],
    }
    layers = {}
    latest_as_of = None
    for name, path in layer_paths.items():
        h = _layer_data_hash(path)
        as_of = _file_mtime_iso(path) if path.is_file() else (
            _file_mtime_iso(next(path.glob("*.tif"), Path())) if path.is_dir() and list(path.glob("*.tif")) else None
        )
        if h or as_of:
            layers[name] = {"sha256": h, "data_as_of": as_of, "path": str(path.relative_to(REPO_ROOT))}
            if as_of and (latest_as_of is None or as_of > latest_as_of):
                latest_as_of = as_of
    return {"layers": layers, "data_as_of": latest_as_of}


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
    data_audit = _collect_data_layers(paths)

    dem_dir = REPO_ROOT / paths["raw"]["dem"]
    dem_files = list(dem_dir.glob("*.tif")) if dem_dir.exists() else []
    rainfall_exists = (REPO_ROOT / paths["raw"]["rainfall"]).exists()

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
    if not dem_files:
        sources.append({"layer": "dem", "provenance": "SYNTHETIC", "url": None,
                        "note": "Synthetic DEM used when Copernicus/SRTM tiles unavailable"})
    elif dem_files:
        manifest_path = REPO_ROOT / paths["raw_dir"] / "download_manifest.json"
        dem_prov = "OPEN_DATA"
        dem_note = "SRTM/Copernicus DEM or terrain-derived from district bbox"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                dem_entry = next((e for e in manifest.get("layers", []) if e.get("layer") == "dem"), None)
                if dem_entry and not dem_entry.get("live"):
                    dem_prov = "DERIVED"
                    dem_note = dem_entry.get("note", dem_note)
            except json.JSONDecodeError:
                pass
        sources.append({"layer": "dem", "provenance": dem_prov, "url": "https://portal.opentopography.org/",
                        "note": dem_note})
    if degraded:
        sources.append({"layer": "rainfall", "provenance": "SYNTHETIC", "url": None,
                        "note": "Uniform rainfall proxy; hazard weights renormalized"})
    elif rainfall_exists:
        rain_prov = "OPEN_DATA"
        rain_note = "CHIRPS/ERA5 or orographic model from DEM"
        manifest_path = REPO_ROOT / paths["raw_dir"] / "download_manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                rain_entry = next((e for e in manifest.get("layers", []) if e.get("layer") == "rainfall"), None)
                if rain_entry and not rain_entry.get("live"):
                    rain_prov = "DERIVED"
                    rain_note = rain_entry.get("note", rain_note)
            except json.JSONDecodeError:
                pass
        sources.append({"layer": "rainfall", "provenance": rain_prov,
                        "url": "https://www.chc.ucsb.edu/data/chirps", "note": rain_note})

    return {
        "district": paths["district"],
        "generated_at": datetime.now(IST).isoformat(),
        "data_as_of": data_audit.get("data_as_of"),
        "pipeline_version": weights.get("pipeline_version", "2.0.0"),
        "model_version": weights["model_version"],
        "weights_version": weights["weights_version"],
        "degraded_mode": degraded,
        "synthetic_data_used": synthetic,
        "data_layers": data_audit.get("layers", {}),
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
        "meta.json", "recommendations.json", "alerts.json",
    ]
    scenarios_src = REPO_ROOT / paths["out_dir"] / "scenarios.json"
    if scenarios_src.exists():
        public_dir = REPO_ROOT / paths["public_data_dir"]
        shutil.copy2(scenarios_src, public_dir / "scenarios.json")
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


def build_export_manifest(paths: dict, copied: list[Path], meta: dict | None = None) -> dict:
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
    result = {
        "generated_at": datetime.now(IST).isoformat(),
        "data_as_of": meta.get("data_as_of") if meta else None,
        "pipeline_version": meta.get("pipeline_version") if meta else None,
        "out_dir": str(out_dir.relative_to(REPO_ROOT)),
        "public_data_dir": str(public_dir.relative_to(REPO_ROOT)),
        "files": entries,
        "parity_ok": all(e["in_sync"] for e in entries),
    }
    if meta and meta.get("data_layers"):
        result["data_layers"] = meta["data_layers"]
    return result


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

    try:
        from _scenario import export_scenarios
        print("Exporting rainfall scenarios...")
        export_scenarios(paths)
    except Exception as e:
        print(f"  [warn] Scenario export failed: {e}")

    manifest = build_export_manifest(paths, copied, meta)
    manifest_path = REPO_ROOT / paths["out_dir"] / "export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    shutil.copy2(manifest_path, REPO_ROOT / paths["public_data_dir"] / "export_manifest.json")
    print(f"  Wrote {manifest_path} (parity_ok={manifest['parity_ok']})")

    copy_to_dist(paths, copied)
    print("05_export.py complete.")


if __name__ == "__main__":
    main()
