"""Scoring formula unit tests."""

import math

import pytest
import yaml
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / "config" / "weights.yaml"


@pytest.fixture
def weights():
    with open(CONFIG) as f:
        return yaml.safe_load(f)


def test_h_ls_range(weights):
    S, L, R = 0.8, 0.6, 0.5
    w = weights["hazard"]["landslide"]
    h_ls = w["slope"] * S + w["landslide_density"] * L + w["rainfall"] * R
    assert 0 <= h_ls <= 1


def test_h_ff_range(weights):
    W, R = 0.7, 0.5
    w = weights["hazard"]["flash_flood"]
    h_ff = w["wetness_stream"] * W + w["rainfall"] * R
    assert 0 <= h_ff <= 1


def test_multi_hazard_formula(weights):
    h_ls, h_ff = 0.78, 0.61
    h = 1 - (1 - h_ls) * (1 - h_ff)
    assert 0 <= h <= 1
    assert h > h_ls
    assert h > h_ff


def test_red_zone_thresholds(weights):
    classes = weights["red_zone_classes"]
    assert classes["red"] == 0.70
    assert classes["orange"] == 0.50
    assert classes["yellow"] == 0.30


def test_priority_bands(weights):
    p = weights["priority"]
    assert p["classes"]["immediate"] == 0.75
    assert p["classes"]["short_term"] == 0.60
    assert p["classes"]["medium_term"] == 0.40


def test_immediate_override(weights):
    force = weights["priority"]["force_immediate"]
    pct_red = 46.0
    h_hab = 0.70
    should_force = pct_red >= force["pct_red_min"] or h_hab >= force["h_hab_min"]
    assert should_force is True


def test_vulnerability_renormalization(weights):
    factors = {"population": 0.8, "isolation": 0.6}
    weights_map = weights["vulnerability"]
    present = {k: weights_map[k] for k in factors}
    total_w = sum(present.values())
    v = sum(factors[k] * (present[k] / total_w) for k in factors)
    assert 0 <= v <= 1


def test_vulnerability_explain_sum(weights):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from _scoring import build_vulnerability_explain, compute_vulnerability

    factors = {
        "population": 0.8,
        "dependents": 0.6,
        "isolation": 0.5,
        "health_access": 0.4,
        "historical_exposure": 0.7,
    }
    v = compute_vulnerability(factors, weights)
    explain = build_vulnerability_explain(factors, weights)
    assert len(explain) == 5
    assert abs(sum(e["contribution"] for e in explain) - v) < 0.01


def test_capacity_never_negative():
    A, p_build, p_slope, p_haz, p_prot = 10.0, 0.7, 0.8, 0.3, 0.0
    a_safe_m2 = A * 10000 * p_build * p_slope * (1 - p_haz) * (1 - p_prot)
    c_raw = a_safe_m2 / 80
    f_road, f_water, f_health = 0.9, 0.85, 0.8
    c = c_raw * f_road * f_water * f_health
    existing = 500
    c_avail = max(0, c - existing)
    assert c_avail >= 0


def test_recommendation_capacity_filter():
    pop = 850
    c_avail = 1120
    min_ratio = 0.5
    assert c_avail >= min_ratio * pop


def test_u_ij_explain_sum(weights):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from _recommendation import build_u_ij_explain
    from _scoring import compute_u_ij

    safety, dist, road, health, school, water, cap = 0.78, 0.85, 0.9, 0.8, 0.65, 0.85, 0.72
    u = compute_u_ij(safety, dist, road, health, school, water, cap, weights)
    explain = build_u_ij_explain(safety, dist, road, health, school, water, cap, weights)
    assert len(explain) == 7
    assert abs(sum(e["contribution"] for e in explain) - u) < 0.01


def test_hazard_bounds():
    for h_ls in [0, 0.5, 1.0]:
        for h_ff in [0, 0.5, 1.0]:
            h = 1 - (1 - h_ls) * (1 - h_ff)
            assert 0 <= h <= 1
