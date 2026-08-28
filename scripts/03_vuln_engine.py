#!/usr/bin/env python3
"""03_vuln_engine.py — Vulnerability, priority, and habitation scoring."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths, load_weights
from _habitation_hazard import sample_habitation_hazards
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


def process_habitations(weights: dict, paths: dict) -> dict:
    landslides_path = REPO_ROOT / paths["out"]["landslides"]
    features = []
    pipeline_count = 0

    for hab in DEMO_HABITATIONS:
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

        h_ls = round(float(sampled["h_ls"] or 0.0), 4)
        h_ff = round(float(sampled["h_ff"] or 0.0), 4)
        h = round(
            float(sampled["h"] if sampled["h"] is not None else compute_multi_hazard(h_ls, h_ff)),
            4,
        )
        pct_red = float(sampled["pct_red"])
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
                "explain": explain,
                "vuln_explain": vuln_explain,
            },
            "geometry": {"type": "Point", "coordinates": [hab["lon"], hab["lat"]]},
        })

    print(f"  {pipeline_count}/{len(DEMO_HABITATIONS)} habitations sampled from hazard pipeline")
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
