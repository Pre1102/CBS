import os
import sys
from typing import List, Dict, Any
import grpc
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.grpc_communication.generated import campus_resource_pb2, campus_resource_pb2_grpc
    from backend.department_nodes.common.config import (
        CSE_GRPC_HOST, CSE_GRPC_PORT,
        IT_GRPC_HOST, IT_GRPC_PORT,
        ENTC_GRPC_HOST, ENTC_GRPC_PORT
    )
except ImportError:
    from grpc_communication.generated import campus_resource_pb2, campus_resource_pb2_grpc
    from department_nodes.common.config import (
        CSE_GRPC_HOST, CSE_GRPC_PORT,
        IT_GRPC_HOST, IT_GRPC_PORT,
        ENTC_GRPC_HOST, ENTC_GRPC_PORT
    )

DEPARTMENT_GRPC_MAP = {
    "CSE": f"{CSE_GRPC_HOST}:{CSE_GRPC_PORT}",
    "IT": f"{IT_GRPC_HOST}:{IT_GRPC_PORT}",
    "E&TC": f"{ENTC_GRPC_HOST}:{ENTC_GRPC_PORT}",
    "ETC": f"{ENTC_GRPC_HOST}:{ENTC_GRPC_PORT}",
    "ENTC": f"{ENTC_GRPC_HOST}:{ENTC_GRPC_PORT}",
}

def resolve_grpc_target(department_code: str) -> str:
    key = department_code.strip().upper()
    target = DEPARTMENT_GRPC_MAP.get(key)
    if not target:
        raise HTTPException(status_code=404, detail=f"Unknown target department for gRPC: {department_code}")
    return target

def get_remote_node_info(target_dept: str, timeout: float = 3.0) -> Dict[str, Any]:
    """
    gRPC Client call: Invokes GetNodeInfo RPC on target department node.
    """
    target_addr = resolve_grpc_target(target_dept)
    try:
        with grpc.insecure_channel(target_addr) as channel:
            stub = campus_resource_pb2_grpc.DepartmentNodeServiceStub(channel)
            request = campus_resource_pb2.NodeInfoRequest(requesting_node="CLIENT")
            response = stub.GetNodeInfo(request, timeout=timeout)
            return {
                "node_name": response.node_name,
                "status": response.status
            }
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to contact {target_dept} node via gRPC ({e.code().name}): {e.details() or 'Server offline'}"
        )

def get_remote_resources(target_dept: str, timeout: float = 3.0) -> List[Dict[str, Any]]:
    """
    gRPC Client call: Invokes GetResources RPC on target department node.
    Converts Protocol Buffer response messages into Python dictionaries.
    """
    target_addr = resolve_grpc_target(target_dept)
    try:
        with grpc.insecure_channel(target_addr) as channel:
            stub = campus_resource_pb2_grpc.DepartmentNodeServiceStub(channel)
            request = campus_resource_pb2.ResourceRequest(department=target_dept)
            response = stub.GetResources(request, timeout=timeout)

            resource_list = []
            for r in response.resources:
                resource_list.append({
                    "id": r.id,
                    "name": r.name,
                    "resource_type": r.resource_type,
                    "location": r.location,
                    "department": r.department,
                    "capacity": r.capacity,
                    "is_available": r.is_available
                })
            return resource_list
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to contact {target_dept} node via gRPC ({e.code().name}): {e.details() or 'Server offline'}"
        )

def send_resource_access_request(target_dept: str, requester_node: str, resource_id: str, timestamp: int, timeout: float = 3.0) -> Dict[str, Any]:
    """
    gRPC Client call (Phase 4): Sends RequestResourceAccess RPC to target department node.
    Returns granted status, responder node name, and message.
    """
    target_addr = resolve_grpc_target(target_dept)
    try:
        with grpc.insecure_channel(target_addr) as channel:
            stub = campus_resource_pb2_grpc.DepartmentNodeServiceStub(channel)
            request = campus_resource_pb2.ResourceAccessRequest(
                requester_node=requester_node,
                resource_id=resource_id,
                timestamp=timestamp
            )
            response = stub.RequestResourceAccess(request, timeout=timeout)
            return {
                "granted": response.granted,
                "responder_node": response.responder_node,
                "message": response.message,
                "timestamp": response.timestamp
            }
    except grpc.RpcError as e:
        return {
            "granted": False,
            "responder_node": target_dept,
            "message": f"gRPC Error ({e.code().name}): {e.details() or 'Server unreachable'}",
            "timestamp": 0
        }

def send_resource_release_request(target_dept: str, requester_node: str, resource_id: str, timestamp: int, timeout: float = 3.0) -> Dict[str, Any]:
    """
    gRPC Client call (Phase 4): Sends ReleaseResourceAccess RPC to target department node.
    """
    target_addr = resolve_grpc_target(target_dept)
    try:
        with grpc.insecure_channel(target_addr) as channel:
            stub = campus_resource_pb2_grpc.DepartmentNodeServiceStub(channel)
            request = campus_resource_pb2.ResourceReleaseRequest(
                requester_node=requester_node,
                resource_id=resource_id,
                timestamp=timestamp
            )
            response = stub.ReleaseResourceAccess(request, timeout=timeout)
            return {
                "success": response.success,
                "responder_node": response.responder_node,
                "message": response.message
            }
    except grpc.RpcError as e:
        return {
            "success": False,
            "responder_node": target_dept,
            "message": f"gRPC Error ({e.code().name}): {e.details() or 'Server unreachable'}"
        }
