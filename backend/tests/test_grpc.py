import os
import tempfile
import time
import pytest
import grpc
from unittest.mock import patch

from backend.department_nodes.common.database import initialize_database
from backend.grpc_communication.server import start_grpc_server
from backend.grpc_communication.node_client import get_remote_node_info, get_remote_resources
from backend.grpc_communication.generated import campus_resource_pb2, campus_resource_pb2_grpc

TEST_GRPC_MAP = {
    "CSE": "127.0.0.1:51051",
    "IT": "127.0.0.1:51052",
    "E&TC": "127.0.0.1:51053",
    "ETC": "127.0.0.1:51053",
    "ENTC": "127.0.0.1:51053"
}

@pytest.fixture(scope="module")
def running_grpc_servers():
    """
    Sets up temporary SQLite databases and starts isolated gRPC servers for CSE, IT, and E&TC nodes on dedicated test ports (51051-51053).
    Patches DEPARTMENT_GRPC_MAP during test execution so node_client functions target test ports.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        cse_db = os.path.join(temp_dir, "cse_test.db")
        it_db = os.path.join(temp_dir, "it_test.db")
        entc_db = os.path.join(temp_dir, "entc_test.db")

        initialize_database(cse_db, "CSE")
        initialize_database(it_db, "IT")
        initialize_database(entc_db, "E&TC")

        # Dedicated test gRPC ports (isolates tests from production ports 50051-50053)
        cse_port = 51051
        it_port = 51052
        entc_port = 51053

        cse_server = start_grpc_server("CSE", cse_port, cse_db)
        it_server = start_grpc_server("IT", it_port, it_db)
        entc_server = start_grpc_server("E&TC", entc_port, entc_db)

        time.sleep(0.5)  # Allow servers to bind and start listening

        with patch.dict("backend.grpc_communication.node_client.DEPARTMENT_GRPC_MAP", TEST_GRPC_MAP):
            yield {
                "CSE": {"port": cse_port, "db": cse_db, "server": cse_server},
                "IT": {"port": it_port, "db": it_db, "server": it_server},
                "E&TC": {"port": entc_port, "db": entc_db, "server": entc_server},
            }

        cse_server.stop(grace=0)
        it_server.stop(grace=0)
        entc_server.stop(grace=0)

def test_grpc_server_starts(running_grpc_servers):
    """Test 1: Verify gRPC server is listening and accepts channel connections on test port 51052."""
    it_port = running_grpc_servers["IT"]["port"]
    channel = grpc.insecure_channel(f"127.0.0.1:{it_port}")
    grpc.channel_ready_future(channel).result(timeout=2.0)
    channel.close()

def test_node_info_rpc(running_grpc_servers):
    """Test 2: Verify GetNodeInfo RPC returns node identity and status on test port 51052."""
    it_port = running_grpc_servers["IT"]["port"]
    with grpc.insecure_channel(f"127.0.0.1:{it_port}") as channel:
        stub = campus_resource_pb2_grpc.DepartmentNodeServiceStub(channel)
        req = campus_resource_pb2.NodeInfoRequest(requesting_node="CSE")
        res = stub.GetNodeInfo(req, timeout=2.0)
        assert res.node_name == "IT"
        assert res.status == "ONLINE"

def test_cse_requests_it_resources_rpc(running_grpc_servers):
    """Test 3: Verify CSE Node client can fetch IT resources via GetResources gRPC RPC on test port 51052."""
    res_list = get_remote_resources("IT")
    assert isinstance(res_list, list)
    assert len(res_list) > 0
    assert any(r["department"] == "IT" for r in res_list)

def test_cse_requests_entc_resources_rpc(running_grpc_servers):
    """Test 4: Verify CSE Node client can fetch E&TC resources via GetResources gRPC RPC on test port 51053."""
    res_list = get_remote_resources("E&TC")
    assert isinstance(res_list, list)
    assert len(res_list) > 0
    assert any(r["department"] == "E&TC" for r in res_list)

def test_returned_resources_correctness(running_grpc_servers):
    """Test 5: Verify returned Protocol Buffer objects strictly belong to target department."""
    it_res = get_remote_resources("IT")
    entc_res = get_remote_resources("E&TC")

    for r in it_res:
        assert r["department"] == "IT", "All IT remote resources must have department = IT"

    for r in entc_res:
        assert r["department"] == "E&TC", "All E&TC remote resources must have department = E&TC"

def test_unavailable_node_error_handling():
    """Test 6: Verify calling an offline gRPC server produces a controlled RpcError / 503 error."""
    # Direct stub call on offline port returns grpc.RpcError (UNAVAILABLE or DEADLINE_EXCEEDED)
    with pytest.raises(grpc.RpcError) as exc_info:
        target_addr = "127.0.0.1:59999"
        with grpc.insecure_channel(target_addr) as channel:
            stub = campus_resource_pb2_grpc.DepartmentNodeServiceStub(channel)
            req = campus_resource_pb2.ResourceRequest(department="OFFLINE_DEPT")
            stub.GetResources(req, timeout=0.5)

    assert exc_info.value.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED)
