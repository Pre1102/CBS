import os
import sys
from typing import List
from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from backend.department_nodes.common.models import ResourceCreate, ResourceResponse
    from backend.department_nodes.common.handlers import get_all_resources, get_resource_by_id, create_resource
except ImportError:
    from department_nodes.common.models import ResourceCreate, ResourceResponse
    from department_nodes.common.handlers import get_all_resources, get_resource_by_id, create_resource

router = APIRouter()
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "it.db"))
NODE_DEPT = "IT"

@router.get("/resources", response_model=List[ResourceResponse])
def list_resources():
    return get_all_resources(DB_PATH)

@router.get("/resources/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: int):
    res = get_resource_by_id(DB_PATH, resource_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Resource ID {resource_id} not found in IT node")
    return res

@router.post("/resources", response_model=ResourceResponse, status_code=201)
def add_resource(resource: ResourceCreate):
    return create_resource(DB_PATH, resource, NODE_DEPT)
