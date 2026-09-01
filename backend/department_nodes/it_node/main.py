import sys
import os
from fastapi import FastAPI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.department_nodes.common.config import IT_HTTP_HOST, IT_HTTP_PORT, IT_GRPC_PORT
    from backend.department_nodes.common.database import initialize_database
    from backend.department_nodes.common.coordination_routes import router as coordination_router
    from backend.department_nodes.it_node.routes.resources import router as resources_router
    from backend.department_nodes.it_node.routes.bookings import router as bookings_router
    from backend.fault_monitoring.routes import router as fault_router
    from backend.fault_monitoring.monitor import NodeHealthMonitor
    from backend.grpc_communication.server import start_grpc_server
    from backend.grpc_communication.coordination import DistributedResourceCoordinator
except ImportError:
    from department_nodes.common.config import IT_HTTP_HOST, IT_HTTP_PORT, IT_GRPC_PORT
    from department_nodes.common.database import initialize_database
    from department_nodes.common.coordination_routes import router as coordination_router
    from department_nodes.it_node.routes.resources import router as resources_router
    from department_nodes.it_node.routes.bookings import router as bookings_router
    from fault_monitoring.routes import router as fault_router
    from fault_monitoring.monitor import NodeHealthMonitor
    from grpc_communication.server import start_grpc_server
    from grpc_communication.coordination import DistributedResourceCoordinator

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database", "it.db"))
NODE_DEPT = "IT"

initialize_database(DB_PATH, NODE_DEPT)

health_monitor = NodeHealthMonitor(NODE_DEPT)
coordinator = DistributedResourceCoordinator(NODE_DEPT, health_monitor=health_monitor)

app = FastAPI(
    title="IT Department Node",
    description="Independent service node for Information Technology department with HTTP, gRPC, Synchronization, and Fault Monitoring."
)

app.state.coordinator = coordinator
app.state.health_monitor = health_monitor

app.include_router(resources_router)
app.include_router(bookings_router)
app.include_router(coordination_router)
app.include_router(fault_router)

grpc_server = None

@app.on_event("startup")
def startup_events():
    global grpc_server
    health_monitor.start()
    try:
        grpc_server = start_grpc_server(NODE_DEPT, IT_GRPC_PORT, DB_PATH, coordinator)
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
        "node": "IT",
        "status": "online",
        "grpc_port": IT_GRPC_PORT,
        "http_port": IT_HTTP_PORT,
        "lamport_clock": coordinator.clock.get_time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=IT_HTTP_HOST, port=IT_HTTP_PORT)
