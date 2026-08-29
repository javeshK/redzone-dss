"""Phase 2C — alerts API tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_alerts_endpoint():
    r = client.get("/api/alerts")
    assert r.status_code == 200
    data = r.json()
    assert "alerts" in data
    assert "alert_count" in data
    assert isinstance(data["alerts"], list)


def test_alerts_have_reasons():
    r = client.get("/api/alerts")
    data = r.json()
    for alert in data["alerts"]:
        assert "reasons" in alert
        assert len(alert["reasons"]) >= 1
        assert alert["habitation_id"]
        assert 0 <= alert["h"] <= 1
