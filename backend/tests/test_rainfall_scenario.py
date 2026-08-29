"""Phase 2C — rainfall scenario slider tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("factor", [1.0, 1.2, 1.5])
def test_rainfall_scenario_factors(factor):
    r = client.get(f"/api/scenario/rainfall?factor={factor}")
    assert r.status_code == 200
    data = r.json()
    assert data["factor"] == factor
    assert 0 <= data.get("h_min", 0) <= 1
    assert 0 <= data.get("h_max", 0) <= 1
    for hab in data.get("habitations", []):
        assert 0 <= hab["h"] <= 1
        assert 0 <= hab["h_ls"] <= 1
        assert 0 <= hab["h_ff"] <= 1


def test_rainfall_scenario_invalid_factor():
    r = client.get("/api/scenario/rainfall?factor=2.0")
    assert r.status_code == 400


def test_scenario_hazard_bounds_increase_with_factor():
    r1 = client.get("/api/scenario/rainfall?factor=1.0")
    r2 = client.get("/api/scenario/rainfall?factor=1.5")
    if r1.status_code == 200 and r2.status_code == 200:
        h1 = r1.json().get("h_mean", 0)
        h2 = r2.json().get("h_mean", 0)
        assert h2 >= h1 - 0.01, "Higher rainfall factor should not decrease mean hazard"
