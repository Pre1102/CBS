from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health")
def get_health():
    """
    Health check endpoint for API Gateway.
    Returns operational status and service identification.
    """
    return {
        "status": "ok",
        "service": "API Gateway"
    }
