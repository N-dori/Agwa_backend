import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Sample valid payload
sample_unit = [{
    "id": "unit1",
    "pods": [{"id": "pod1", "age": 3}],
    "readings": [{
        "id": "r1",
        "pH": 6.5,
        "temp": 22.3,
        "ec": 1.5,
        "timestamp": "2025-06-05T12:00:00"
    }]
}]

# Sample invalid pH payload
invalid_unit = [{
    "id": "unit2",
    "pods": [{"id": "pod2", "age": 4}],
    "readings": [{
        "id": "r2",
        "pH": 4.9,
        "temp": 20.1,
        "ec": 1.4,
        "timestamp": "2025-06-05T12:05:00"
    }]
}]


def test_valid_post_units():
    response = client.post("/api/sensor", json=sample_unit)
    assert response.status_code == 200
    data = response.json()
    assert data[0]['classification']['classification'] == 'Healthy'


def test_invalid_post_units_classification():
    response = client.post("/api/sensor", json=invalid_unit)
    assert response.status_code == 200
    data = response.json()
    assert data[0]['classification']['classification'] == 'Needs Attention'


def test_alerts_endpoint_for_invalid_readings():
    # First post the unit with invalid reading
    client.post("/api/sensor", json=invalid_unit)

    # Then check alerts for that unit
    response = client.get("/api/alerts", params={"unitId": "unit2"})
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) == 1
    assert alerts[0]["pH"] < 5.5


def test_alerts_endpoint_with_no_alerts():
    client.post("/api/sensor", json=sample_unit)
    response = client.get("/api/alerts", params={"unitId": "unit1"})
    assert response.status_code == 200
    assert response.json() == []


def test_alerts_missing_unit():
    response = client.get("/api/alerts", params={"unitId": "unknown"})
    assert response.status_code == 200
    assert response.json() == []
