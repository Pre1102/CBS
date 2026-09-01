from fastapi.testclient import TestClient
from backend.api_gateway.main import app as gateway_app

client = TestClient(gateway_app)

def test_gateway_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Campus Resource Booking System API"}

def test_gateway_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "API Gateway"}

def test_gateway_unknown_department():
    response = client.get("/api/departments/unknown_dept/resources")
    assert response.status_code == 404
    assert "Unknown department" in response.json()["detail"]
