from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/coordination", tags=["Distributed Coordination"])

class CoordinationRequestPayload(BaseModel):
    resource_id: str = "SHARED-SEMINAR-HALL"

@router.post("/request")
def request_shared_resource(payload: CoordinationRequestPayload, request: Request):
    """
    Triggers Ricart-Agrawala distributed mutual exclusion request for a shared resource.
    Node broadcasts gRPC RequestResourceAccess to all peer nodes using Lamport timestamps.
    """
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        raise HTTPException(status_code=500, detail="Distributed coordinator not initialized on this node")

    success, msg = coordinator.request_access(payload.resource_id)
    if not success and "already in state" in msg:
        raise HTTPException(status_code=409, detail=msg)
    
    return {
        "success": success,
        "message": msg,
        "status": coordinator.get_status()
    }

@router.post("/release")
def release_shared_resource(payload: CoordinationRequestPayload, request: Request):
    """
    Releases critical section for a shared resource and notifies deferred peer requests.
    """
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        raise HTTPException(status_code=500, detail="Distributed coordinator not initialized on this node")

    success, msg = coordinator.release_access(payload.resource_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": success,
        "message": msg,
        "status": coordinator.get_status()
    }

@router.get("/status")
def get_coordination_status(request: Request):
    """
    Returns current node coordination state, Lamport logical clock, and deferred queue status.
    """
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        raise HTTPException(status_code=500, detail="Distributed coordinator not initialized on this node")

    return coordinator.get_status()
