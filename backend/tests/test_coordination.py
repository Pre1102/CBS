import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.grpc_communication.lamport_clock import LamportClock
from backend.grpc_communication.coordination import DistributedResourceCoordinator

def test_1_lamport_clock_initial_zero():
    """Test 1: Lamport clock starts at zero."""
    clock = LamportClock()
    assert clock.get_time() == 0

def test_2_lamport_clock_increment():
    """Test 2: Lamport clock increments correctly."""
    clock = LamportClock(0)
    t1 = clock.increment()
    t2 = clock.increment()
    assert t1 == 1
    assert t2 == 2
    assert clock.get_time() == 2

def test_3_lamport_clock_update_remote():
    """Test 3: Receiving a remote timestamp updates local clock to max(local, remote) + 1."""
    clock = LamportClock(5)
    # Remote timestamp is 10 > 5 -> expected 11
    t = clock.update(10)
    assert t == 11
    assert clock.get_time() == 11

    # Remote timestamp is 3 < 11 -> expected 12
    t2 = clock.update(3)
    assert t2 == 12

def test_4_request_ordering_tuple():
    """Test 4: Request ordering strictly uses (timestamp, node_name)."""
    req1 = (10, "CSE")
    req2 = (10, "IT")
    req3 = (11, "CSE")

    assert req1 < req2  # Same timestamp, "CSE" < "IT" tie-breaker
    assert req1 < req3  # 10 < 11
    assert req2 < req3  # 10 < 11

def test_5_earlier_request_gets_priority():
    """Test 5: Earlier request (lower timestamp) gets priority."""
    coord = DistributedResourceCoordinator("IT", initial_clock=15)
    coord.state = "REQUESTING"
    coord.current_resource = "SHARED-SEMINAR-HALL"
    coord.request_timestamp = 10  # Local request has timestamp 10

    # Incoming request from CSE with timestamp 20 (later/lower priority)
    granted, msg = coord.handle_incoming_request("CSE", "SHARED-SEMINAR-HALL", timestamp=20)
    assert granted is False
    assert "deferred" in msg.lower()
    assert len(coord.deferred_requests) == 1
    assert coord.deferred_requests[0] == ("CSE", "SHARED-SEMINAR-HALL", 20)

def test_6_later_request_is_deferred():
    """Test 6: Incoming request with higher timestamp is deferred when local node is REQUESTING."""
    coord = DistributedResourceCoordinator("CSE", initial_clock=5)
    coord.state = "REQUESTING"
    coord.current_resource = "SHARED-SEMINAR-HALL"
    coord.request_timestamp = 5

    # Incoming request with timestamp 10
    granted, _ = coord.handle_incoming_request("E&TC", "SHARED-SEMINAR-HALL", 10)
    assert granted is False
    assert len(coord.deferred_requests) == 1

def test_7_deferred_request_released():
    """Test 7: Deferred request is cleared and returned after current node releases critical section."""
    coord = DistributedResourceCoordinator("CSE", initial_clock=5)
    coord.state = "IN_CRITICAL_SECTION"
    coord.current_resource = "SHARED-SEMINAR-HALL"
    coord.request_timestamp = 5

    # Incoming request deferred
    coord.handle_incoming_request("IT", "SHARED-SEMINAR-HALL", 10)
    assert len(coord.deferred_requests) == 1

    # Release critical section
    success, msg = coord.release_access("SHARED-SEMINAR-HALL")
    assert success is True
    assert coord.state == "IDLE"
    assert coord.current_resource is None
    assert len(coord.deferred_requests) == 0
    assert "1 deferred requests notified" in msg

def test_8_entry_requires_all_permissions():
    """Test 8: Node enters IN_CRITICAL_SECTION only after receiving required peer permissions."""
    coord = DistributedResourceCoordinator("CSE", initial_clock=0)

    # Mock send_resource_access_request to grant permissions from IT and E&TC
    with patch("backend.grpc_communication.coordination.send_resource_access_request") as mock_send:
        mock_send.side_effect = lambda target_dept, **kwargs: {
            "granted": True,
            "responder_node": target_dept,
            "message": "Permission granted",
            "timestamp": 1
        }

        success, msg = coord.request_access("SHARED-SEMINAR-HALL")
        assert success is True
        assert coord.state == "IN_CRITICAL_SECTION"
        assert coord.received_replies == {"IT", "E&TC"}

def test_9_release_critical_section():
    """Test 9: Node releases critical section correctly."""
    coord = DistributedResourceCoordinator("IT")
    coord.state = "IN_CRITICAL_SECTION"
    coord.current_resource = "SHARED-SEMINAR-HALL"

    success, msg = coord.release_access("SHARED-SEMINAR-HALL")
    assert success is True
    assert coord.state == "IDLE"

def test_10_unavailable_peer_handled_safely():
    """Test 10: Node handles unavailable peer during request without crashing."""
    coord = DistributedResourceCoordinator("CSE", initial_clock=0)

    with patch("backend.grpc_communication.coordination.send_resource_access_request") as mock_send:
        # IT grants permission, but E&TC is offline
        mock_send.side_effect = lambda target_dept, **kwargs: (
            {"granted": True, "responder_node": "IT", "message": "Granted", "timestamp": 1}
            if target_dept == "IT"
            else {"granted": False, "responder_node": "E&TC", "message": "Server unreachable", "timestamp": 0}
        )

        success, msg = coord.request_access("SHARED-SEMINAR-HALL")
        assert success is False
        assert coord.state == "REQUESTING"
        assert "Waiting for peer permissions" in msg

def test_11_simulated_concurrent_requests_deterministic():
    """Test 11: Two simulated concurrent requests produce deterministic ordering based on (timestamp, node_name)."""
    cse_coord = DistributedResourceCoordinator("CSE", initial_clock=10)
    it_coord = DistributedResourceCoordinator("IT", initial_clock=10)

    # Both set to REQUESTING with identical timestamp 10
    cse_coord.state = "REQUESTING"
    cse_coord.current_resource = "SHARED-SEMINAR-HALL"
    cse_coord.request_timestamp = 10

    it_coord.state = "REQUESTING"
    it_coord.current_resource = "SHARED-SEMINAR-HALL"
    it_coord.request_timestamp = 10

    # CSE handles IT's request: priority (10, "CSE") < (10, "IT") -> CSE defers IT
    granted_to_it, _ = cse_coord.handle_incoming_request("IT", "SHARED-SEMINAR-HALL", 10)
    assert granted_to_it is False
    assert len(cse_coord.deferred_requests) == 1

    # IT handles CSE's request: priority (10, "CSE") < (10, "IT") -> IT grants CSE
    granted_to_cse, _ = it_coord.handle_incoming_request("CSE", "SHARED-SEMINAR-HALL", 10)
    assert granted_to_cse is True
    assert len(it_coord.deferred_requests) == 0
