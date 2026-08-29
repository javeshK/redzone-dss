"""Phase 2B — refresh status API tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_refresh_status_endpoint():
    r = client.get("/api/meta/refresh-status")
    assert r.status_code == 200
    data = r.json()
    assert "pipeline_version" in data
    assert "success" in data
    assert "steps" in data


def test_district_meta_has_data_as_of():
    r = client.get("/api/district")
    assert r.status_code == 200
    meta = r.json()["meta"]
    assert "data_as_of" in meta
    assert "pipeline_version" in meta
