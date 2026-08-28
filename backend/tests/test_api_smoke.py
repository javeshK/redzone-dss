"""API smoke tests for RedZone DSS."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["district"] == "Rudraprayag"
    assert data["data_loaded"] is True


def test_district():
    r = client.get("/api/district")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Rudraprayag"
    assert len(data["bbox"]) == 4
    assert "geojson" in data


def test_habitations_list():
    r = client.get("/api/habitations")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 25
    assert "id" in data[0]
    assert "priority" in data[0]


def test_habitation_detail():
    r = client.get("/api/habitations/UT_RUD_0001")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Ukhimath"
    assert len(data["explain"]) > 0
    assert len(data["vuln_explain"]) >= 5
    assert data["hazard_source"] in ("PIPELINE", "FALLBACK")


def test_habitation_not_found():
    r = client.get("/api/habitations/INVALID")
    assert r.status_code == 404


def test_layer_red_zones():
    r = client.get("/api/layers/red_zones")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0


@pytest.mark.parametrize("layer_name", ["district", "habitations", "landslides", "streams", "sites"])
def test_layer_endpoints(layer_name):
    r = client.get(f"/api/layers/{layer_name}")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"


def test_layer_not_found():
    r = client.get("/api/layers/invalid_layer")
    assert r.status_code == 404


def test_habitations_have_hazard_scores():
    r = client.get("/api/habitations")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 25
    for hab in data:
        assert 0 <= hab["h"] <= 1
        assert 0 <= hab["h_ls"] <= 1
        assert 0 <= hab["h_ff"] <= 1
        assert 0 <= hab["v"] <= 1


def test_sites():
    r = client.get("/api/sites")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 8
    assert "capacity_available" in data[0]
    assert data[0]["screening_note"] == "First-order physical screening capacity"


def test_recommendations_coverage():
    r = client.get("/api/habitations")
    habs = r.json()
    rec_count = 0
    for hab in habs:
        rr = client.get(f"/api/recommend/{hab['id']}")
        if rr.status_code == 200:
            rec_count += 1
    assert rec_count >= 20


def test_recommendation():
    r = client.get("/api/recommend/UT_RUD_0001")
    assert r.status_code == 200
    data = r.json()
    assert data["top"]["site_id"]
    assert data["runner_up"] is not None
    assert len(data["top"]["reasons"]) >= 3
    assert len(data["top"]["explain"]) == 7
    assert data["comparison"] is not None
    assert data["comparison"]["score_delta"] > 0
    assert len(data["comparison"]["notes"]) >= 1
