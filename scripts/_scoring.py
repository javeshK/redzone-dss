"""Scoring engine — hazard, vulnerability, priority, capacity, recommendation."""

from __future__ import annotations

from typing import Any


def compute_h_ls(s: float, l: float, r: float, weights: dict) -> float:
    w = weights["hazard"]["landslide"]
    return w["slope"] * s + w["landslide_density"] * l + w["rainfall"] * r


def compute_h_ff(w: float, r: float, weights: dict) -> float:
    wf = weights["hazard"]["flash_flood"]
    return wf["wetness_stream"] * w + wf["rainfall"] * r


def compute_multi_hazard(h_ls: float, h_ff: float) -> float:
    return 1 - (1 - h_ls) * (1 - h_ff)


def classify_zone(h: float, weights: dict) -> str:
    classes = weights["red_zone_classes"]
    if h >= classes["red"]:
        return "Red"
    if h >= classes["orange"]:
        return "Orange"
    if h >= classes["yellow"]:
        return "Yellow"
    return "Green"


def compute_vulnerability(factors: dict[str, float], weights: dict) -> float:
    """Weighted sum with renormalization for missing factors."""
    vw = weights["vulnerability"]
    present = {k: vw[k] for k in factors if k in vw}
    if not present:
        return 0.0
    total_w = sum(present.values())
    return sum(factors[k] * (present[k] / total_w) for k in present)


def compute_priority(h_hab: float, v: float, weights: dict) -> float:
    p = weights["priority"]
    return p["hazard"] * h_hab + p["vulnerability"] * v


def classify_priority(
    p: float, pct_red: float, h_hab: float, weights: dict
) -> str:
    force = weights["priority"]["force_immediate"]
    if pct_red >= force["pct_red_min"] or h_hab >= force["h_hab_min"]:
        return "Immediate"
    classes = weights["priority"]["classes"]
    if p >= classes["immediate"]:
        return "Immediate"
    if p >= classes["short_term"]:
        return "Short-term"
    if p >= classes["medium_term"]:
        return "Medium-term"
    return "Monitor"


def compute_capacity(
    area_ha: float,
    p_buildable: float,
    p_slope_lt15: float,
    p_hazard: float,
    p_protected: float,
    f_road: float,
    f_water: float,
    f_health: float,
    existing_pop: int,
    weights: dict,
) -> tuple[int, int]:
    # A_safe in hectares; convert to m² for 80 m²/person standard
    a_safe_ha = area_ha * p_buildable * p_slope_lt15 * (1 - p_hazard) * (1 - p_protected)
    a_safe_m2 = a_safe_ha * 10000
    ha_per_person = weights["capacity"]["ha_per_person"]
    c_raw = a_safe_m2 / ha_per_person
    c = int(c_raw * f_road * f_water * f_health)
    c_avail = max(0, c - existing_pop)
    return c, c_avail


def compute_u_ij(
    safety: float,
    distance_score: float,
    road: float,
    healthcare: float,
    school: float,
    water: float,
    capacity_fit: float,
    weights: dict,
) -> float:
    rw = weights["recommendation"]
    return (
        rw["safety"] * safety
        + rw["distance"] * distance_score
        + rw["road"] * road
        + rw["healthcare"] * healthcare
        + rw["school"] * school
        + rw["water"] * water
        + rw["capacity_fit"] * capacity_fit
    )


def build_vulnerability_explain(factors: dict[str, float], weights: dict) -> list[dict[str, Any]]:
    """Per-factor vulnerability breakdown with renormalized weights."""
    vw = weights["vulnerability"]
    present = {k: vw[k] for k in factors if k in vw}
    if not present:
        return []
    total_w = sum(present.values())
    explain = []
    for key in present:
        w_norm = present[key] / total_w
        val = factors[key]
        explain.append({
            "factor": key,
            "value": round(val, 4),
            "weight": round(w_norm, 4),
            "contribution": round(w_norm * val, 4),
        })
    return explain


def build_explain(h: float, v: float, weights: dict, pct_red: float = 0) -> list[dict[str, Any]]:
    p_cfg = weights["priority"]
    explain = [
        {
            "factor": "multi_hazard",
            "value": round(h, 4),
            "weight": p_cfg["hazard"],
            "contribution": round(p_cfg["hazard"] * h, 4),
        },
        {
            "factor": "vulnerability",
            "value": round(v, 4),
            "weight": p_cfg["vulnerability"],
            "contribution": round(p_cfg["vulnerability"] * v, 4),
        },
    ]
    force = p_cfg["force_immediate"]
    if pct_red >= force["pct_red_min"]:
        explain.append({
            "factor": "pct_red_override",
            "value": pct_red,
            "weight": 0.0,
            "contribution": 0.0,
            "note": f"pct_red >= {force['pct_red_min']}% forces Immediate",
        })
    elif h >= force["h_hab_min"]:
        explain.append({
            "factor": "h_hab_override",
            "value": h,
            "weight": 0.0,
            "contribution": 0.0,
            "note": f"H_hab >= {force['h_hab_min']} forces Immediate",
        })
    return explain
