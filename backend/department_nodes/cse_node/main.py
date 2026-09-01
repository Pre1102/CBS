import sys
import os
from fastapi import FastAPI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.department_nodes.common.config import CSE_HTTP_HOST, CSE_HTTP_PORT, CSE_GRPC_PORT
    from backend.department_nodes.common.database import initialize_database
    from backend.department_nodes.common.coordination_routes import router as coordination_router
    from backend.department_nodes.cse_node.routes.resources import router as resources_router
    from backend.department_nodes.cse_node.routes.bookings import router as bookings_router
    from backend.department_nodes.cse_node.routes.remote import router as remote_router
    from backend.fault_monitoring.routes import router as fault_router
    from backend.fault_monitoring.monitor import NodeHealthMonitor
    from backend.grpc_communication.server import start_grpc_server
    from backend.grpc_communication.coordination import DistributedResourceCoordinator
except ImportError:
    from department_nodes.common.config import CSE_HTTP_HOST, CSE_HTTP_PORT, CSE_GRPC_PORT
    from department_nodes.common.database import initialize_database
    from department_nodes.common.coordination_routes import router as coordination_router
    from department_nodes.cse_node.routes.resources import router as resources_router
    from department_nodes.cse_node.routes.bookings import router as bookings_router
    from department_nodes.cse_node.routes.remote import router as remote_router
    from fault_monitoring.routes import router as fault_router
    from fault_monitoring.monitor import NodeHealthMonitor
    from grpc_communication.server import start_grpc_server
    from grpc_communication.coordination import DistributedResourceCoordinator

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database", "cse.db"))
NODE_DEPT = "CSE"

initialize_database(DB_PATH, NODE_DEPT)

health_monitor = NodeHealthMonitor(NODE_DEPT)
coordinator = DistributedResourceCoordinator(NODE_DEPT, health_monitor=health_monitor)

app = FastAPI(
    title="CSE Department Node",
    description="Independent service node for Computer Science & Engineering department with HTTP, gRPC, Synchronization, and Fault Monitoring."
)

app.state.coordinator = coordinator
app.state.health_monitor = health_monitor

app.include_router(resources_router)
app.include_router(bookings_router)
app.include_router(remote_router)
app.include_router(coordination_router)
app.include_router(fault_router)

grpc_server = None

@app.on_event("startup")
def startup_events():
    global grpc_server
    health_monitor.start()
    try:
        grpc_server = start_grpc_server(NODE_DEPT, CSE_GRPC_PORT, DB_PATH, coordinator)
    except Exception:
        pass

@app.on_event("shutdown")
def shutdown_events():
    global grpc_server
    health_monitor.stop()
    if grpc_server:
        grpc_server.stop(grace=0)

@app.get("/health")
def get_health():
    return {
        "node": "CSE",
        "status": "online",
        "grpc_port": CSE_GRPC_PORT,
        "http_port": CSE_HTTP_PORT,
        "lamport_clock": coordinator.clock.get_time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=CSE_HTTP_HOST, port=CSE_HTTP_PORT)
