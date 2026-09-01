import os
import tempfile
from fastapi.testclient import TestClient

from backend.department_nodes.cse_node.main import app as cse_app
from backend.department_nodes.it_node.main import app as it_app
from backend.department_nodes.common.database import initialize_database
from backend.department_nodes.common.handlers import get_all_resources, create_resource

client_cse = TestClient(cse_app)
client_it = TestClient(it_app)

def test_get_resources():
    response = client_cse.get("/resources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_single_resource():
    response = client_cse.get("/resources/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["department"] == "CSE"

def test_create_resource_success():
    payload = {
        "name": "CSE New Robotics Lab",
        "resource_type": "Laboratory",
        "location": "CSE Block - Floor 3",
        "department": "CSE",
        "capacity": 30,
        "is_available": True
    }
    response = client_cse.post("/resources", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "CSE New Robotics Lab"

def test_create_resource_department_mismatch():
    payload = {
        "name": "IT Lab inside CSE",
        "resource_type": "Laboratory",
        "location": "CSE Block",
        "department": "IT",  # Mismatch: posting to CSE node with department=IT
        "capacity": 30,
        "is_available": True
    }
    response = client_cse.post("/resources", json=payload)
    assert response.status_code == 400
    assert "Department mismatch" in response.json()["detail"]

def test_data_isolation_between_nodes():
    """Verify CSE node resources and IT node resources are completely isolated."""
    cse_res = client_cse.get("/resources").json()
    it_res = client_it.get("/resources").json()

    cse_depts = set(r["department"] for r in cse_res)
    it_depts = set(r["department"] for r in it_res)

    assert cse_depts == {"CSE"}, "CSE node must contain only CSE resources"
    assert it_depts == {"IT"}, "IT node must contain only IT resources"
