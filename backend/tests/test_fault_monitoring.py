import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.fault_monitoring.monitor import NodeHealthMonitor
from backend.grpc_communication.coordination import DistributedResourceCoordinator

def test_1_peer_initial_state_unknown():
    """Test 1: New peer starts as UNKNOWN."""
    monitor = NodeHealthMonitor("CSE")
    status = monitor.get_status()
    assert status["node"] == "CSE"
    assert status["peers"]["IT"]["status"] == "UNKNOWN"
    assert status["peers"]["E&TC"]["status"] == "UNKNOWN"

def test_2_successful_health_check_marks_online():
    """Test 2: Successful health check marks peer ONLINE."""
    monitor = NodeHealthMonitor("CSE")
    monitor.record_success("IT")
    status = monitor.get_status()
    assert status["peers"]["IT"]["status"] == "ONLINE"
    assert status["peers"]["IT"]["failure_count"] == 0
    assert status["peers"]["IT"]["last_success"] is not None

def test_3_single_failure_below_threshold():
    """Test 3: One failed health check does not immediately mark peer OFFLINE if threshold > 1."""
    monitor = NodeHealthMonitor("CSE", failure_threshold=3)
    monitor.record_success("IT")  # Start ONLINE
    
    # 1 failure < threshold
    monitor.record_failure("IT")
    status = monitor.get_status()
    assert status["peers"]["IT"]["status"] == "ONLINE"
    assert status["peers"]["IT"]["failure_count"] == 1

def test_4_consecutive_failures_reach_threshold_offline():
    """Test 4: Consecutive failures reaching the threshold mark peer OFFLINE."""
    monitor = NodeHealthMonitor("CSE", failure_threshold=3)
    monitor.record_failure("IT")
    monitor.record_failure("IT")
    assert monitor.get_status()["peers"]["IT"]["status"] == "UNKNOWN"  # Not yet 3

    monitor.record_failure("IT")  # 3rd failure reaches threshold
    assert monitor.get_status()["peers"]["IT"]["status"] == "OFFLINE"
    assert monitor.get_status()["peers"]["IT"]["failure_count"] == 3

def test_5_recovery_marks_peer_online():
    """Test 5: Successful check after failure marks peer ONLINE."""
    monitor = NodeHealthMonitor("CSE", failure_threshold=3)
    monitor.record_failure("IT")
    monitor.record_failure("IT")
    monitor.record_failure("IT")
    assert monitor.get_status()["peers"]["IT"]["status"] == "OFFLINE"

    # Recovery
    monitor.record_success("IT")
    assert monitor.get_status()["peers"]["IT"]["status"] == "ONLINE"

def test_6_failure_counter_resets_on_recovery():
    """Test 6: Failure counter resets to 0 after successful recovery."""
    monitor = NodeHealthMonitor("CSE", failure_threshold=3)
    monitor.record_failure("IT")
    monitor.record_failure("IT")
    assert monitor.get_status()["peers"]["IT"]["failure_count"] == 2

    monitor.record_success("IT")
    assert monitor.get_status()["peers"]["IT"]["failure_count"] == 0

def test_7_health_endpoint_available():
    """Test 7: Health endpoint structure remains valid."""
    from backend.department_nodes.cse_node.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["node"] == "CSE"
    assert data["status"] == "online"

def test_8_grpc_communication_failure_handled_safely():
    """Test 8: gRPC communication failure is handled without crashing the node."""
    coord = DistributedResourceCoordinator("CSE")
    
    with patch("backend.grpc_communication.coordination.send_resource_access_request") as mock_send:
        # Simulate gRPC RPC error / unreachable peer
        mock_send.return_value = {
            "granted": False,
            "responder_node": "IT",
            "message": "gRPC connection error: server unreachable",
            "timestamp": 0
        }
        
        success, msg = coord.request_access("SHARED-SEMINAR-HALL")
        assert success is False
        assert coord.state == "REQUESTING"
        assert "Waiting for peer permissions" in msg

def test_9_coordination_does_not_falsely_grant_when_peer_offline():
    """Test 9: Distributed coordination does not falsely enter critical section when required peer is offline."""
    monitor = NodeHealthMonitor("CSE", failure_threshold=3)
    # Mark IT as OFFLINE
    monitor.record_failure("IT")
    monitor.record_failure("IT")
    monitor.record_failure("IT")
    assert monitor.is_peer_online("IT") is False

    coord = DistributedResourceCoordinator("CSE", health_monitor=monitor)

    with patch("backend.grpc_communication.coordination.send_resource_access_request") as mock_send:
        mock_send.side_effect = lambda target_dept, **kwargs: {
            "granted": True,
            "responder_node": target_dept,
            "message": "Granted",
            "timestamp": 1
        }
        
        success, msg = coord.request_access("SHARED-SEMINAR-HALL")
        assert success is False
        assert coord.state == "REQUESTING"
        assert "IT" not in coord.received_replies

def test_10_recovered_node_returns_to_normal_communication():
    """Test 10: Recovered node returns to normal communication and can grant access."""
    monitor = NodeHealthMonitor("CSE", failure_threshold=3)
    # Mark IT OFFLINE then ONLINE (Recovery)
    for _ in range(3):
        monitor.record_failure("IT")
    assert monitor.is_peer_online("IT") is False
    
    monitor.record_success("IT")
    assert monitor.is_peer_online("IT") is True

    coord = DistributedResourceCoordinator("CSE", health_monitor=monitor)
    with patch("backend.grpc_communication.coordination.send_resource_access_request") as mock_send:
        mock_send.side_effect = lambda target_dept, **kwargs: {
            "granted": True,
            "responder_node": target_dept,
            "message": "Granted",
            "timestamp": 1
        }

        success, msg = coord.request_access("SHARED-SEMINAR-HALL")
        assert success is True
        assert coord.state == "IN_CRITICAL_SECTION"
        assert coord.received_replies == {"IT", "E&TC"}
