import os
import sys
from typing import List
from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from backend.department_nodes.common.models import ResourceResponse
    from backend.grpc_communication.node_client import get_remote_resources, get_remote_node_info
except ImportError:
    from department_nodes.common.models import ResourceResponse
    from grpc_communication.node_client import get_remote_resources, get_remote_node_info

router = APIRouter()

@router.get("/remote-resources/{target_dept}", response_model=List[ResourceResponse])
def fetch_remote_resources_via_grpc(target_dept: str):
    """
    Demonstration Endpoint for Phase 3:
    The CSE Node acts as a gRPC Client to request resource inventory from a target remote node (e.g. IT or E&TC) using gRPC Remote Procedure Calls.
    Flow: Client -> CSE Node (HTTP 50151) -> gRPC Client -> Target Node gRPC Server (50052/50053) -> Target SQLite DB -> gRPC Response -> CSE Node -> Client.
    """
    dept_key = target_dept.strip().upper()
    if dept_key in ["CSE"]:
        raise HTTPException(status_code=400, detail="Use local /resources endpoint to query CSE local node")
    
    # Inter-node gRPC Remote Procedure Call
    return get_remote_resources(dept_key)

@router.get("/remote-node-info/{target_dept}")
def fetch_remote_node_info_via_grpc(target_dept: str):
    """
    Demonstration Endpoint for Phase 3:
    Invokes GetNodeInfo RPC on remote department node.
    """
    dept_key = target_dept.strip().upper()
    return get_remote_node_info(dept_key)
