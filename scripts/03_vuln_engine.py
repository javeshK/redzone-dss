#!/usr/bin/env python3
"""03_vuln_engine.py — Vulnerability, priority, and habitation scoring."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths, load_weights
from _crs import COMPUTE_CRS, DISPLAY_CRS
from _habitation_hazard import sample_habitation_hazards, HAB_BUFFER_M
from _scoring import (
    build_explain,
    build_vulnerability_explain,
    classify_priority,
    classify_zone,
    compute_multi_hazard,
    compute_priority,
    compute_vulnerability,
)
from _vulnerability import compute_vulnerability_factors
from demo_habitations import DEMO_HABITATIONS


def load_habitation_sources(paths: dict) -> list[dict]:
    """Load habitations from village polygons when available, else demo list."""
    villages_path = REPO_ROOT / paths["raw"]["villages"]
    if villages_path.exists():
        try:
            villages = gpd.read_file(villages_path)
            if villages.crs is None:
                villages = villages.set_crs(DISPLAY_CRS)
            villages_utm = villages.to_crs(COMPUTE_CRS)
            sources = []
            for hab in DEMO_HABITATIONS:
                pt = Point(hab["lon"], hab["lat"])
                pt_gdf = gpd.GeoDataFrame(geometry=[pt], crs=DISPLAY_CRS).to_crs(COMPUTE_CRS)
                pt_utm = pt_gdf.geometry.iloc[0]
                joined = villages_utm[villages_utm.geometry.contains(pt_utm)]
                if joined.empty:
                    joined = villages_utm[villages_utm.distance(pt_utm) < 5000]
                    if not joined.empty:
                        joined = joined.nsmallest(1, villages_utm.distance(pt_utm))
                if not joined.empty:
                    row = joined.iloc[0]
                    centroid = joined.geometry.iloc[0].centroid
                    name_col = next((c for c in ("name", "village", "VILLAGE", "NAME") if c in joined.columns), None)
                    name = str(row[name_col]) if name_col else hab["name"]
                    sources.append({
                        **hab,
                        "name": name,
                        "lon": centroid.x if centroid.x < 180 else hab["lon"],
                        "lat": centroid.y if centroid.y < 90 else hab["lat"],
                        "village_joined": True,
                    })
                else:
                    sources.append({**hab, "village_joined": False})
            joined_count = sum(1 for s in sources if s.get("village_joined"))
            print(f"  Village polygon join: {joined_count}/{len(sources)} habitations matched")
            return sources
        except Exception as e:
            print(f"  [warn] Village join failed: {e}")
    return [{**h, "village_joined": False} for h in DEMO_HABITATIONS]


def compute_pct_red_polygon(lon: float, lat: float, red_zones_path: Path, village_geom=None) -> float:
    """Compute pct_red from village polygon or 300 m buffer."""
    if not red_zones_path.exists():
        return 0.0
    rz = gpd.read_file(red_zones_path)
    if rz.empty or "zone_class" not in rz.columns:
        return 0.0
    rz_utm = rz.to_crs(COMPUTE_CRS)
    red = rz_utm[rz_utm["zone_class"] == "Red"]
    if red.empty:
        return 0.0

    if village_geom is not None:
        area_geom = village_geom
        if area_geom.geom_type == "Point":
            area_geom = area_geom.buffer(HAB_BUFFER_M)
    else:
        hab = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs=DISPLAY_CRS).to_crs(COMPUTE_CRS)
        area_geom = hab.geometry.iloc[0].buffer(HAB_BUFFER_M)

    area = area_geom.area
    if area <= 0:
        return 0.0
    red_area = red.intersection(area_geom).area.sum()
    return round(float(red_area / area * 100.0), 1)


def process_habitations(weights: dict, paths: dict) -> dict:
    landslides_path = REPO_ROOT / paths["out"]["landslides"]
    rz_path = REPO_ROOT / paths["out"]["red_zones"]
    villages_path = REPO_ROOT / paths["raw"]["villages"]
    villages_gdf = None
    if villages_path.exists():
        try:
            villages_gdf = gpd.read_file(villages_path)
            if villages_gdf.crs is None:
                villages_gdf = villages_gdf.set_crs(DISPLAY_CRS)
            villages_gdf = villages_gdf.to_crs(COMPUTE_CRS)
        except Exception:
            villages_gdf = None

    hab_sources = load_habitation_sources(paths)
    features = []
    pipeline_count = 0

    for hab in hab_sources:
        factors = compute_vulnerability_factors(hab, DEMO_HABITATIONS, landslides_path)
        sampled = sample_habitation_hazards(
            hab["lon"],
            hab["lat"],
            paths,
            REPO_ROOT,
            fallback=None,
        )
        if sampled["from_pipeline"]:
            pipeline_count += 1

        village_geom = None
        if villages_gdf is not None:
            pt = gpd.GeoDataFrame(geometry=[Point(hab["lon"], hab["lat"])], crs=DISPLAY_CRS).to_crs(COMPUTE_CRS)
            pt_utm = pt.geometry.iloc[0]
            matched = villages_gdf[villages_gdf.geometry.contains(pt_utm)]
            if matched.empty:
                matched = villages_gdf[villages_gdf.distance(pt_utm) < 5000].nsmallest(1, villages_gdf.distance(pt_utm))
            if not matched.empty:
                village_geom = matched.geometry.iloc[0]

        pct_red = compute_pct_red_polygon(hab["lon"], hab["lat"], rz_path, village_geom)
        if pct_red == 0.0 and sampled["pct_red"] > 0:
            pct_red = sampled["pct_red"]

        h_ls = round(float(sampled["h_ls"] or 0.0), 4)
        h_ff = round(float(sampled["h_ff"] or 0.0), 4)
        h = round(
            float(sampled["h"] if sampled["h"] is not None else compute_multi_hazard(h_ls, h_ff)),
            4,
        )
        v = compute_vulnerability(factors, weights)
        p = compute_priority(h, v, weights)
        priority = classify_priority(p, pct_red, h, weights)
        zone = classify_zone(h, weights)
        explain = build_explain(h, v, weights, pct_red)
        vuln_explain = build_vulnerability_explain(factors, weights)

        features.append({
            "type": "Feature",
            "properties": {
                "id": hab["id"],
                "name": hab["name"],
                "block": hab["block"],
                "pop": hab["pop"],
                "h_ls": h_ls,
                "h_ff": h_ff,
                "h": h,
                "v": round(v, 4),
                "p": round(p, 4),
                "priority": priority,
                "pct_red": pct_red,
                "zone_class": zone,
                "source": "EXPERT_SCREENED",
                "hazard_source": "PIPELINE" if sampled["from_pipeline"] else "FALLBACK",
                "village_joined": hab.get("village_joined", False),
                "explain": explain,
                "vuln_explain": vuln_explain,
            },
            "geometry": {"type": "Point", "coordinates": [hab["lon"], hab["lat"]]},
        })

    print(f"  {pipeline_count}/{len(hab_sources)} habitations sampled from hazard pipeline")
    immediate = sum(1 for f in features if f["properties"]["priority"] == "Immediate")
    print(f"  Priority: {immediate} Immediate, {len(features) - immediate} other")
    return {"type": "FeatureCollection", "name": "habitations", "features": features}


def main():
    weights = load_weights()
    paths = load_paths()

    print("Computing vulnerability and priority...")
    fc = process_habitations(weights, paths)
    out_path = REPO_ROOT / paths["out"]["habitations"]
    out_path.write_text(json.dumps(fc, indent=2), encoding="utf-8")
    print(f"  Wrote {len(fc['features'])} habitations to {out_path}")
    print("03_vuln_engine.py complete.")


if __name__ == "__main__":
    main()
