from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="", tags=["Fault Monitoring"])

@router.get("/fault-status")
def get_fault_status(request: Request):
    """
    Returns current node fault-monitoring state and observed peer health statuses.
    """
    monitor = getattr(request.app.state, "health_monitor", None)
    if not monitor:
        raise HTTPException(status_code=500, detail="Health monitor not initialized on this node")
    return monitor.get_status()
