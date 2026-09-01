import sys
import os
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.api_gateway.main import app
except ImportError:
    from api_gateway.main import app

client = TestClient(app)

def test_get_root():
    """
    Test the API Gateway root GET endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Campus Resource Booking System API"}

def test_get_health():
    """
    Test the API Gateway health check endpoint.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "API Gateway"
    }
