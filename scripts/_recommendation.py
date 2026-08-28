"""U_ij scoring helpers and recommendation explain builders."""

from __future__ import annotations

from typing import Any


def build_u_ij_explain(
    safety: float,
    distance_score: float,
    road: float,
    healthcare: float,
    school: float,
    water: float,
    capacity_fit: float,
    weights: dict,
) -> list[dict[str, Any]]:
    rw = weights["recommendation"]
    factors = [
        ("safety", safety, rw["safety"]),
        ("distance", distance_score, rw["distance"]),
        ("road", road, rw["road"]),
        ("healthcare", healthcare, rw["healthcare"]),
        ("school", school, rw["school"]),
        ("water", water, rw["water"]),
        ("capacity_fit", capacity_fit, rw["capacity_fit"]),
    ]
    return [
        {
            "factor": name,
            "value": round(val, 4),
            "weight": weight,
            "contribution": round(weight * val, 4),
        }
        for name, val, weight in factors
    ]


def build_site_reasons(
    hab_name: str,
    pop: int,
    site: dict,
    dist_km: float,
    dist_score: float,
    c_avail: int,
    u_score: float,
    max_hazard: float,
    min_capacity_ratio: float,
    meets_capacity: bool,
) -> list[str]:
    min_cap = int(min_capacity_ratio * pop)
    reasons = [
        f"H_site={site['p_hazard']:.2f} (below {max_hazard} safety filter)",
        f"Distance {dist_km:.1f} km from {hab_name} (proximity score {dist_score:.2f})",
        (
            f"Access: road {site['f_road']:.2f}, healthcare {site['f_health']:.2f}, "
            f"water {site['f_water']:.2f}, school {site.get('f_school', 0.65):.2f}"
        ),
        f"First-order physical screening capacity: {c_avail} available (habitation pop {pop})",
    ]
    if meets_capacity:
        reasons.append(f"Capacity meets 0.5×population threshold ({c_avail} ≥ {min_cap})")
    else:
        reasons.append(
            f"Below full capacity threshold ({c_avail} < {min_cap}) — split relocation may be required"
        )
    reasons.append(f"U_ij suitability score {u_score:.2f}")
    return reasons


def build_comparison(top: dict, runner_up: dict, hab_pop: int) -> dict[str, Any]:
    score_delta = round(top["score"] - runner_up["score"], 4)
    dist_delta = round(runner_up["distance_km"] - top["distance_km"], 2)
    cap_delta = top["capacity_available"] - runner_up["capacity_available"]
    notes = [
        f"Top site U_ij={top['score']:.2f} vs runner-up {runner_up['score']:.2f} (Δ +{score_delta:.2f})",
    ]
    if dist_delta > 0:
        notes.append(f"Top site is {dist_delta:.1f} km closer to the habitation")
    elif dist_delta < 0:
        notes.append(f"Runner-up is {abs(dist_delta):.1f} km closer, but lower overall U_ij")
    if cap_delta > 0:
        notes.append(f"Top site has {cap_delta} more available screening capacity")
    elif cap_delta < 0:
        notes.append(
            f"Runner-up has {abs(cap_delta)} more capacity; top site wins on safety/access balance"
        )
    if top["safety"] < runner_up["safety"]:
        notes.append(
            f"Lower site hazard at top choice (H={top['safety']:.2f} vs {runner_up['safety']:.2f})"
        )
    return {
        "score_delta": score_delta,
        "distance_delta_km": dist_delta,
        "capacity_delta": cap_delta,
        "notes": notes,
    }
