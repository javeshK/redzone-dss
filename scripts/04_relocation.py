#!/usr/bin/env python3
"""04_relocation.py — Site screening, capacity, U_ij ranking, recommendations."""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths, load_weights
from _scoring import compute_capacity, compute_u_ij
from _recommendation import build_comparison, build_site_reasons, build_u_ij_explain
from _site_screening import enrich_site_from_rasters
from demo_sites import DEMO_SITES

IST = timezone(timedelta(hours=5, minutes=30))
DISTANCE_MAX_KM = 25.0


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def distance_score(dist_km: float, max_km: float = DISTANCE_MAX_KM) -> float:
    return max(0.0, 1.0 - dist_km / max_km)


def capacity_fit_score(c_avail: int, pop: int) -> float:
    if pop <= 0:
        return 0.0
    return min(1.0, c_avail / pop)


def screen_site(site: dict, weights: dict) -> bool:
    screening = weights["site_screening"]
    slope_deg = site.get("slope_mean_deg", (1 - site["p_slope_lt15"]) * 30)
    return (
        site["p_hazard"] < screening["max_mean_hazard"]
        and slope_deg < screening["max_mean_slope_deg"]
        and site["p_protected"] < 0.5
        and site["area_ha"] >= screening["min_residual_area_ha"]
    )


def prepare_sites(paths: dict, weights: dict) -> tuple[list[dict], list[dict]]:
    """Enrich and screen sites; return (passed, rejected)."""
    passed, rejected = [], []
    for raw in DEMO_SITES:
        site = enrich_site_from_rasters(raw, paths, REPO_ROOT)
        if screen_site(site, weights):
            passed.append(site)
        else:
            site["reject_reason"] = "Failed hazard/slope/area/protected screening"
            rejected.append(site)
    return passed, rejected


def rank_sites_for_habitation(
    hab: dict, sites: list[dict], weights: dict
) -> tuple[list[dict], list[dict]]:
    """Return (eligible ranked, all screened ranked)."""
    pop = hab["pop"]
    min_ratio = weights["recommendation"]["min_capacity_ratio"]
    max_haz = weights["site_screening"]["max_mean_hazard"]
    eligible: list[dict] = []
    all_ranked: list[dict] = []

    for site in sites:
        c, c_avail = compute_capacity(
            site["area_ha"],
            site["p_buildable"],
            site["p_slope_lt15"],
            site["p_hazard"],
            site["p_protected"],
            site["f_road"],
            site["f_water"],
            site["f_health"],
            site["existing_pop"],
            weights,
        )
        dist = haversine_km(hab["lon"], hab["lat"], site["lon"], site["lat"])
        dist_scr = distance_score(dist)
        safety_score = 1.0 - site["p_hazard"]
        cap_fit = capacity_fit_score(c_avail, pop)
        u = compute_u_ij(
            safety_score,
            dist_scr,
            site["f_road"],
            site["f_health"],
            site.get("f_school", 0.65),
            site["f_water"],
            cap_fit,
            weights,
        )
        meets_cap = c_avail >= min_ratio * pop
        entry = {
            "site_id": site["id"],
            "site_name": site["name"],
            "score": round(u, 4),
            "safety": round(site["p_hazard"], 4),
            "distance_km": round(dist, 2),
            "road_access": site["f_road"],
            "healthcare_access": site["f_health"],
            "water_access": site["f_water"],
            "school_access": site.get("f_school", 0.65),
            "capacity": c,
            "capacity_available": c_avail,
            "meets_capacity_threshold": meets_cap,
            "explain": build_u_ij_explain(
                safety_score,
                dist_scr,
                site["f_road"],
                site["f_health"],
                site.get("f_school", 0.65),
                site["f_water"],
                cap_fit,
                weights,
            ),
            "reasons": build_site_reasons(
                hab["name"],
                pop,
                site,
                dist,
                dist_scr,
                c_avail,
                u,
                max_haz,
                min_ratio,
                meets_cap,
            ),
        }
        all_ranked.append(entry)
        if meets_cap:
            eligible.append(entry)

    eligible.sort(key=lambda x: x["score"], reverse=True)
    all_ranked.sort(key=lambda x: x["score"], reverse=True)
    return eligible, all_ranked


def build_sites_geojson(sites: list[dict], weights: dict) -> dict:
    features = []
    for site in sites:
        c, c_avail = compute_capacity(
            site["area_ha"],
            site["p_buildable"],
            site["p_slope_lt15"],
            site["p_hazard"],
            site["p_protected"],
            site["f_road"],
            site["f_water"],
            site["f_health"],
            site["existing_pop"],
            weights,
        )
        features.append({
            "type": "Feature",
            "properties": {
                "id": site["id"],
                "name": site["name"],
                "h_mean": site["p_hazard"],
                "slope_mean_deg": site.get("slope_mean_deg", round((1 - site["p_slope_lt15"]) * 30, 1)),
                "area_ha": site["area_ha"],
                "p_buildable": site["p_buildable"],
                "p_protected": site["p_protected"],
                "capacity": c,
                "capacity_available": c_avail,
                "existing_population": site["existing_pop"],
                "f_road": site["f_road"],
                "f_water": site["f_water"],
                "f_health": site["f_health"],
                "source": "EXPERT_SCREENED",
                "hazard_source": site.get("hazard_source", "EXPERT_SCREENED"),
                "screening_note": "First-order physical screening capacity",
                "screened": True,
            },
            "geometry": {"type": "Point", "coordinates": [site["lon"], site["lat"]]},
        })
    return {"type": "FeatureCollection", "name": "candidate_sites", "features": features}


def pick_recommendation(hab: dict, eligible: list[dict], all_ranked: list[dict]) -> tuple[dict, dict | None]:
    if eligible:
        top = eligible[0]
        if len(eligible) > 1:
            return top, eligible[1]
        if len(all_ranked) > 1:
            runner = next((s for s in all_ranked if s["site_id"] != top["site_id"]), None)
            return top, runner
        return top, None
    if len(all_ranked) >= 2:
        top = {**all_ranked[0]}
        top["reasons"] = top["reasons"] + [
            f"Split recommendation: no single site has capacity for full population ({hab['pop']})",
            "Combine with runner-up for partial relocation",
        ]
        return top, all_ranked[1]
    if all_ranked:
        return all_ranked[0], None
    raise ValueError(f"No ranked sites for {hab['name']}")


def main():
    weights = load_weights()
    paths = load_paths()

    hab_path = REPO_ROOT / paths["out"]["habitations"]
    habitations = json.loads(hab_path.read_text(encoding="utf-8"))

    print("Screening candidate sites...")
    screened, rejected = prepare_sites(paths, weights)
    print(f"  {len(screened)} passed screening, {len(rejected)} rejected")

    print("Building sites GeoJSON...")
    sites_fc = build_sites_geojson(screened, weights)
    sites_out = REPO_ROOT / paths["out"]["sites"]
    sites_out.write_text(json.dumps(sites_fc, indent=2), encoding="utf-8")
    print(f"  Wrote {len(sites_fc['features'])} sites to {sites_out}")

    print("Computing recommendations...")
    recommendations = {}
    for feat in habitations["features"]:
        props = feat["properties"]
        hab = {
            "id": props["id"],
            "name": props["name"],
            "pop": props["pop"],
            "lon": feat["geometry"]["coordinates"][0],
            "lat": feat["geometry"]["coordinates"][1],
        }
        try:
            eligible, all_ranked = rank_sites_for_habitation(hab, screened, weights)
            top, runner_up = pick_recommendation(hab, eligible, all_ranked)
        except ValueError:
            continue
        recommendations[hab["id"]] = {
            "hab_id": hab["id"],
            "hab_name": hab["name"],
            "top": top,
            "runner_up": runner_up,
            "comparison": build_comparison(top, runner_up, hab["pop"]) if runner_up else None,
        }
        props["rec_site_id"] = top["site_id"]
        props["rec_score"] = top["score"]
        props["why_site"] = top["reasons"]

    rec_out = REPO_ROOT / paths["out"]["recommendations"]
    rec_data = {
        "generated_at": datetime.now(IST).isoformat(),
        "model_version": weights["model_version"],
        "recommendations": recommendations,
    }
    rec_out.write_text(json.dumps(rec_data, indent=2), encoding="utf-8")
    hab_path.write_text(json.dumps(habitations, indent=2), encoding="utf-8")
    print(f"  Wrote {len(recommendations)} recommendations for {len(habitations['features'])} habitations")
    print("04_relocation.py complete.")


if __name__ == "__main__":
    main()
