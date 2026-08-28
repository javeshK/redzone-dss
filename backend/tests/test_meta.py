"""Meta and KPI integration tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_district_meta_kpis():
    r = client.get("/api/district")
    assert r.status_code == 200
    data = r.json()
    meta = data["meta"]
    assert meta["district"] == "Rudraprayag"
    assert meta["model_version"]
    assert meta["weights_version"]
    assert len(meta["limitations"]) >= 3
    assert len(meta["sources"]) >= 5

    kpis = meta["kpis"]
    assert kpis["habitation_count"] >= 25
    assert kpis["site_count"] >= 8
    assert kpis["immediate_count"] >= 0
    assert kpis["district_area_ha"] > 0


def test_meta_flags_are_boolean():
    r = client.get("/api/district")
    meta = r.json()["meta"]
    assert isinstance(meta["degraded_mode"], bool)
    assert isinstance(meta["synthetic_data_used"], bool)


def test_health_reflects_loaded_data():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["data_loaded"] is True
    assert data["district"] == "Rudraprayag"
