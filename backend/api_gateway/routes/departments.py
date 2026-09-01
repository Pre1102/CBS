import os
import sys
import httpx
from typing import Any
from fastapi import APIRouter, HTTPException, Request, Response

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.department_nodes.common.config import (
        CSE_HTTP_HOST, CSE_HTTP_PORT,
        IT_HTTP_HOST, IT_HTTP_PORT,
        ENTC_HTTP_HOST, ENTC_HTTP_PORT
    )
except ImportError:
    from department_nodes.common.config import (
        CSE_HTTP_HOST, CSE_HTTP_PORT,
        IT_HTTP_HOST, IT_HTTP_PORT,
        ENTC_HTTP_HOST, ENTC_HTTP_PORT
    )

router = APIRouter()

DEPARTMENT_MAP = {
    "cse": f"http://{CSE_HTTP_HOST}:{CSE_HTTP_PORT}",
    "it": f"http://{IT_HTTP_HOST}:{IT_HTTP_PORT}",
    "entc": f"http://{ENTC_HTTP_HOST}:{ENTC_HTTP_PORT}",
    "e&tc": f"http://{ENTC_HTTP_HOST}:{ENTC_HTTP_PORT}",
    "etc": f"http://{ENTC_HTTP_HOST}:{ENTC_HTTP_PORT}",
}

def resolve_node_url(department: str) -> str:
    key = department.strip().lower()
    url = DEPARTMENT_MAP.get(key)
    if not url:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown department '{department}'. Supported departments: cse, it, entc"
        )
    return url

@router.get("/api/departments/status")
async def get_departments_status():
    """
    Returns online/offline health status for all department nodes.
    Used by React dashboard.
    """
    node_targets = [
        ("CSE", DEPARTMENT_MAP["cse"]),
        ("IT", DEPARTMENT_MAP["it"]),
        ("E&TC", DEPARTMENT_MAP["entc"])
    ]
    results = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for dept_name, base_url in node_targets:
            try:
                res = await client.get(f"{base_url}/health")
                if res.status_code == 200:
                    results[dept_name] = "ONLINE"
                else:
                    results[dept_name] = "OFFLINE"
            except Exception:
                results[dept_name] = "OFFLINE"
    return results

@router.get("/api/departments/{department}/resources")
async def forward_get_resources(department: str):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(f"{base_url}/resources")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.get("/api/departments/{department}/remote-resources/{target_dept}")
async def forward_get_remote_resources_via_grpc(department: str, target_dept: str):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=4.0) as client:
        try:
            resp = await client.get(f"{base_url}/remote-resources/{target_dept}")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

# Phase 4 Coordination Endpoints Forwarding
@router.post("/api/departments/{department}/coordination/request")
async def forward_coordination_request(department: str, request: Request):
    base_url = resolve_node_url(department)
    body = await request.json()
    async with httpx.AsyncClient(timeout=4.0) as client:
        try:
            resp = await client.post(f"{base_url}/coordination/request", json=body)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.post("/api/departments/{department}/coordination/release")
async def forward_coordination_release(department: str, request: Request):
    base_url = resolve_node_url(department)
    body = await request.json()
    async with httpx.AsyncClient(timeout=4.0) as client:
        try:
            resp = await client.post(f"{base_url}/coordination/release", json=body)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.get("/api/departments/{department}/coordination/status")
async def forward_coordination_status(department: str):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(f"{base_url}/coordination/status")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.get("/api/departments/{department}/fault-status")
async def forward_fault_status(department: str):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(f"{base_url}/fault-status")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.get("/api/departments/{department}/resources/{resource_id}")
async def forward_get_resource_by_id(department: str, resource_id: int):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(f"{base_url}/resources/{resource_id}")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.post("/api/departments/{department}/resources")
async def forward_create_resource(department: str, request: Request):
    base_url = resolve_node_url(department)
    body = await request.json()
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.post(f"{base_url}/resources", json=body)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.get("/api/departments/{department}/bookings")
async def forward_get_bookings(department: str):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(f"{base_url}/bookings")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.get("/api/departments/{department}/bookings/{booking_id}")
async def forward_get_booking_by_id(department: str, booking_id: int):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(f"{base_url}/bookings/{booking_id}")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.post("/api/departments/{department}/bookings")
async def forward_create_booking(department: str, request: Request):
    base_url = resolve_node_url(department)
    body = await request.json()
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.post(f"{base_url}/bookings", json=body)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")

@router.put("/api/departments/{department}/bookings/{booking_id}/cancel")
async def forward_cancel_booking(department: str, booking_id: int):
    base_url = resolve_node_url(department)
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.put(f"{base_url}/bookings/{booking_id}/cancel")
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Department node '{department}' is currently unreachable")
