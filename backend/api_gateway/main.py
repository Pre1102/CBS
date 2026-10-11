import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure parent directory is on sys.path for direct script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.api_gateway.routes.health import router as health_router
    from backend.api_gateway.routes.departments import router as departments_router
    from backend.api_gateway.routes.simulation import router as simulation_router
    from backend.department_nodes.common.config import GATEWAY_HOST, GATEWAY_PORT
except ImportError:
    from api_gateway.routes.health import router as health_router
    from api_gateway.routes.departments import router as departments_router
    from api_gateway.routes.simulation import router as simulation_router
    from department_nodes.common.config import GATEWAY_HOST, GATEWAY_PORT

app = FastAPI(
    title="Campus Resource Booking System - API Gateway",
    description="Central API Gateway entry point for frontend requests."
)

frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

# Configure CORS to permit requests from local React Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        *frontend_origins,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(departments_router)
app.include_router(simulation_router)

@app.get("/")
def get_root():
    """
    Root endpoint confirming API Gateway is active.
    """
    return {
        "message": "Campus Resource Booking System API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=GATEWAY_HOST, port=GATEWAY_PORT)
