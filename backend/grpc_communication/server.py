import os
import sys
from concurrent import futures
import grpc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.grpc_communication.generated import campus_resource_pb2, campus_resource_pb2_grpc
    from backend.department_nodes.common.handlers import get_all_resources
except ImportError:
    from grpc_communication.generated import campus_resource_pb2, campus_resource_pb2_grpc
    from department_nodes.common.handlers import get_all_resources

class DepartmentNodeServicer(campus_resource_pb2_grpc.DepartmentNodeServiceServicer):
    """
    gRPC Servicer implementation for department nodes.
    Responds to Phase 3 data queries and Phase 4 Ricart-Agrawala coordination RPCs.
    """
    def __init__(self, department_code: str, db_path: str, coordinator=None):
        self.department_code = department_code
        self.db_path = db_path
        self.coordinator = coordinator

    def GetNodeInfo(self, request, context):
        """RPC 1: Returns node identity and online status."""
        return campus_resource_pb2.NodeInfoResponse(
            node_name=self.department_code,
            status="ONLINE"
        )

    def GetResources(self, request, context):
        """
        RPC 2: Returns list of resources owned by this department node.
        Reads strictly from local SQLite database.
        """
        raw_resources = get_all_resources(self.db_path)
        resource_protos = []

        for r in raw_resources:
            proto_item = campus_resource_pb2.ResourceProto(
                id=r["id"],
                name=r["name"],
                resource_type=r["resource_type"],
                location=r["location"],
                department=r["department"],
                capacity=r["capacity"],
                is_available=bool(r["is_available"])
            )
            resource_protos.append(proto_item)

        return campus_resource_pb2.ResourceResponse(
            department=self.department_code,
            resources=resource_protos
        )

    def RequestResourceAccess(self, request, context):
        """
        RPC 3 (Phase 4): Evaluates incoming Ricart-Agrawala mutual exclusion request from a peer.
        """
        if self.coordinator:
            granted, msg = self.coordinator.handle_incoming_request(
                requester_node=request.requester_node,
                resource_id=request.resource_id,
                timestamp=request.timestamp
            )
            current_clock = self.coordinator.clock.get_time()
        else:
            granted, msg, current_clock = True, "No local coordinator active", 0

        return campus_resource_pb2.ResourceAccessResponse(
            granted=granted,
            responder_node=self.department_code,
            message=msg,
            timestamp=current_clock
        )

    def ReleaseResourceAccess(self, request, context):
        """
        RPC 4 (Phase 4): Receives notification that a peer has released a shared resource.
        """
        if self.coordinator:
            self.coordinator.clock.update(request.timestamp)

        return campus_resource_pb2.ResourceReleaseResponse(
            success=True,
            responder_node=self.department_code,
            message=f"Release of resource {request.resource_id} acknowledged by {self.department_code}"
        )

def start_grpc_server(department_code: str, grpc_port: int, db_path: str, coordinator=None):
    """
    Instantiates and starts a gRPC server listening on the specified port.
    Returns the running gRPC server object.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = DepartmentNodeServicer(department_code, db_path, coordinator)
    campus_resource_pb2_grpc.add_DepartmentNodeServiceServicer_to_server(servicer, server)
    
    server.add_insecure_port(f"0.0.0.0:{grpc_port}")
    server.start()
    return server
