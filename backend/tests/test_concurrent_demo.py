import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.grpc_communication.simulation import (
    SimulationRequest,
    run_concurrent_conflict_simulation,
    PRESET_RESOURCES
)

def test_preset_resources_loaded():
    """Verify curated preset resources list is populated."""
    assert len(PRESET_RESOURCES) >= 3
    ids = [r["id"] for r in PRESET_RESOURCES]
    assert "SHARED-SEMINAR-HALL" in ids
    assert "CENTRAL-AUDITORIUM" in ids

def test_simultaneous_requests_tie_breaker():
    """
    Test 1: Simultaneous requests (0ms delay) with equal initial clocks.
    Tie-breaking rule: (timestamp, 'CSE') < (timestamp, 'IT') -> CSE wins.
    """
    config = SimulationRequest(
        dept_a="CSE",
        dept_b="IT",
        resource_id="SHARED-SEMINAR-HALL",
        booking_date="2026-10-15",
        start_time="14:00",
        end_time="16:00",
        requester_a="Prof. CSE",
        requester_b="Dr. IT",
        stagger_delay_ms=0,
        initial_clock_a=5,
        initial_clock_b=5
    )

    res = run_concurrent_conflict_simulation(config)
    assert res["success"] is True
    assert res["winner_department"] == "CSE"
    assert res["loser_department"] == "IT"
    assert res["winner_timestamp"] == 6
    assert res["loser_timestamp"] == 6
    assert "'CSE'" in res["priority_rule"] and "'IT'" in res["priority_rule"]
    assert res["loser_status"] == "DOUBLE_BOOKING_PREVENTED"
    assert res["winner_booking_id"] is not None

def test_staggered_delay_earlier_node_wins():
    """
    Test 2: Staggered launch where Department B (IT) has lower timestamp.
    IT starts with initial clock 2, CSE with initial clock 8.
    IT's request timestamp is 3 < 9 -> IT wins.
    """
    config = SimulationRequest(
        dept_a="CSE",
        dept_b="IT",
        resource_id="CENTRAL-AUDITORIUM",
        booking_date="2026-10-20",
        start_time="09:00",
        end_time="11:00",
        requester_a="Prof. CSE",
        requester_b="Dr. IT",
        stagger_delay_ms=20,
        initial_clock_a=8,
        initial_clock_b=2
    )

    res = run_concurrent_conflict_simulation(config)
    assert res["success"] is True
    assert res["winner_department"] == "IT"
    assert res["loser_department"] == "CSE"
    assert res["winner_timestamp"] == 3
    assert res["loser_timestamp"] == 9
    assert res["loser_status"] == "DOUBLE_BOOKING_PREVENTED"

def test_department_pair_it_vs_entc():
    """Test 3: Simulation works with IT vs E&TC pair."""
    config = SimulationRequest(
        dept_a="IT",
        dept_b="E&TC",
        resource_id="HPC-CLUSTER-LAB",
        booking_date="2026-11-05",
        start_time="11:00",
        end_time="13:00",
        requester_a="Dr. IT Lead",
        requester_b="Prof. ENTC Lead",
        stagger_delay_ms=0,
        initial_clock_a=4,
        initial_clock_b=4
    )

    res = run_concurrent_conflict_simulation(config)
    assert res["success"] is True
    assert res["winner_department"] in ["IT", "E&TC"]
    assert res["loser_department"] in ["IT", "E&TC"]
    assert res["winner_department"] != res["loser_department"]
    assert res["loser_status"] == "DOUBLE_BOOKING_PREVENTED"

def test_lamport_clock_progression_in_trace():
    """Test 4: Verify Lamport Clock ticks and receive max updates in event trace."""
    config = SimulationRequest(
        dept_a="CSE",
        dept_b="E&TC",
        resource_id="SHARED-SEMINAR-HALL",
        booking_date="2026-12-01",
        start_time="10:00",
        end_time="12:00",
        requester_a="Prof. CSE",
        requester_b="Prof. ENTC",
        stagger_delay_ms=10,
        initial_clock_a=1,
        initial_clock_b=1
    )

    res = run_concurrent_conflict_simulation(config)
    trace = res["event_trace"]
    assert len(trace) >= 8

    # Find GRPC_RECV events
    recv_events = [e for e in trace if e["event_type"] == "GRPC_RECV"]
    assert len(recv_events) == 2
    for r in recv_events:
        assert r["lamport_clock_after"] > r["lamport_clock_before"]

def test_same_department_rejected():
    """Test 5: Selecting the same department for both nodes raises ValueError."""
    config = SimulationRequest(
        dept_a="CSE",
        dept_b="CSE",
        resource_id="SHARED-SEMINAR-HALL"
    )

    with pytest.raises(ValueError, match="Simulation requires two distinct department nodes"):
        run_concurrent_conflict_simulation(config)
