from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_liveness_returns_alive():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

def test_metadata_endpoint():
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    assert response.json()["name"] == "InsiderShield"
