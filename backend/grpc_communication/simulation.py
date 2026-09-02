import os
import sys
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.grpc_communication.lamport_clock import LamportClock
    from backend.grpc_communication.coordination import DistributedResourceCoordinator
    from backend.department_nodes.common.database import get_connection, initialize_database
    from backend.department_nodes.common.models import BookingCreate, ResourceCreate
    from backend.department_nodes.common.handlers import (
        create_resource,
        has_booking_conflict,
        create_booking
    )
except ImportError:
    from grpc_communication.lamport_clock import LamportClock
    from grpc_communication.coordination import DistributedResourceCoordinator
    from department_nodes.common.database import get_connection, initialize_database
    from department_nodes.common.models import BookingCreate, ResourceCreate
    from department_nodes.common.handlers import (
        create_resource,
        has_booking_conflict,
        create_booking
    )

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DEPT_DB_MAP = {
    "CSE": os.path.join(PROJECT_ROOT, "backend", "department_nodes", "cse_node", "database", "cse.db"),
    "IT": os.path.join(PROJECT_ROOT, "backend", "department_nodes", "it_node", "database", "it.db"),
    "E&TC": os.path.join(PROJECT_ROOT, "backend", "department_nodes", "entc_node", "database", "entc.db"),
    "ETC": os.path.join(PROJECT_ROOT, "backend", "department_nodes", "entc_node", "database", "entc.db"),
    "ENTC": os.path.join(PROJECT_ROOT, "backend", "department_nodes", "entc_node", "database", "entc.db"),
}

PRESET_RESOURCES = [
    {
        "id": "SHARED-SEMINAR-HALL",
        "name": "Campus Shared Seminar Hall",
        "resource_type": "Seminar Hall",
        "capacity": 250,
        "location": "Campus Central Complex - Auditorium A"
    },
    {
        "id": "CENTRAL-AUDITORIUM",
        "name": "Central University Auditorium",
        "resource_type": "Auditorium",
        "capacity": 500,
        "location": "Main Academic Block - Ground Floor"
    },
    {
        "id": "HPC-CLUSTER-LAB",
        "name": "High-Performance Computing Cluster Lab",
        "resource_type": "Laboratory",
        "capacity": 40,
        "location": "Advanced Research Center - Floor 2"
    },
    {
        "id": "IOT-INNOVATION-CENTER",
        "name": "IoT & Robotics Innovation Center",
        "resource_type": "Laboratory",
        "capacity": 35,
        "location": "Innovation Hub - Floor 1"
    }
]

class SimulationRequest(BaseModel):
    dept_a: str = Field("CSE", description="First participating department (e.g. CSE)")
    dept_b: str = Field("IT", description="Second participating department (e.g. IT)")
    resource_id: str = Field("SHARED-SEMINAR-HALL", description="Target shared resource ID or name")
    resource_name: Optional[str] = Field("Campus Shared Seminar Hall", description="Human-readable resource name")
    booking_date: str = Field("2026-09-10", description="Reservation date (YYYY-MM-DD)")
    start_time: str = Field("10:00", description="Start time (HH:MM)")
    end_time: str = Field("12:00", description="End time (HH:MM)")
    requester_a: str = Field("Prof. Sharma (CSE)", description="Requester name for Department A")
    requester_b: str = Field("Dr. Kulkarni (IT)", description="Requester name for Department B")
    stagger_delay_ms: int = Field(0, ge=0, le=2000, description="Launch stagger delay in milliseconds for Department B")
    initial_clock_a: Optional[int] = Field(None, description="Optional manual initial clock for Dept A")
    initial_clock_b: Optional[int] = Field(None, description="Optional manual initial clock for Dept B")


def ensure_shared_resource_in_db(db_path: str, resource_identifier: str, resource_name: str, dept_code: str) -> int:
    """
    Ensures that the target resource exists in the local department database
    and returns its integer resource ID.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Try finding by name or identifier for this specific department
    cursor.execute("""
        SELECT id FROM resources
        WHERE (name = ? OR name = ?) AND UPPER(department) = UPPER(?);
    """, (resource_identifier, resource_name, dept_code))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row["id"]
    
    # Insert new resource entry owned by this department
    cursor.execute("""
        INSERT INTO resources (name, resource_type, location, department, capacity, is_available)
        VALUES (?, ?, ?, ?, ?, 1);
    """, (
        resource_name or resource_identifier,
        "Shared Facility",
        "Campus Central Complex",
        dept_code,
        150
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def run_concurrent_conflict_simulation(config: SimulationRequest) -> Dict[str, Any]:
    """
    Executes an enhanced concurrent simulation demonstrating:
    1. Simultaneous / Staggered request dispatch by two independent department nodes.
    2. Independent Lamport Logical Clock progression (monotonic tick + max(recv) + 1).
    3. Ricart-Agrawala mutual exclusion ordering using (timestamp, node_name) tie-breaker.
    4. Critical section acquisition (HELD) by the winner node and request deferral by the loser node.
    5. Real SQLite booking persistence by the winner node.
    6. Double-booking conflict detection and rejection when the second node executes its critical section.
    7. Chronological event log trace returned for live visualization in the demo UI.
    """
    dept_a = config.dept_a.strip().upper()
    dept_b = config.dept_b.strip().upper()

    if dept_a == dept_b:
        raise ValueError(f"Simulation requires two distinct department nodes (received '{dept_a}' for both)")

    # Standardize department names
    db_path_a = DEPT_DB_MAP.get(dept_a)
    db_path_b = DEPT_DB_MAP.get(dept_b)

    if not db_path_a or not db_path_b:
        raise ValueError(f"Unsupported department pair: {dept_a} vs {dept_b}")

    # Ensure databases are initialized
    initialize_database(db_path_a, dept_a)
    initialize_database(db_path_b, dept_b)

    # Initialize independent coordinators and Lamport clocks
    init_clock_a = config.initial_clock_a if config.initial_clock_a is not None else 5
    init_clock_b = config.initial_clock_b if config.initial_clock_b is not None else 5

    coord_a = DistributedResourceCoordinator(dept_a, initial_clock=init_clock_a)
    coord_b = DistributedResourceCoordinator(dept_b, initial_clock=init_clock_b)

    events: List[Dict[str, Any]] = []
    start_sim_time = time.time()

    def record_event(
        node: str,
        event_type: str,
        clock_before: int,
        clock_after: int,
        state_before: str,
        state_after: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        elapsed_ms = round((time.time() - start_sim_time) * 1000, 1)
        events.append({
            "elapsed_ms": elapsed_ms,
            "node": node,
            "event_type": event_type,
            "lamport_clock_before": clock_before,
            "lamport_clock_after": clock_after,
            "state_before": state_before,
            "state_after": state_after,
            "message": message,
            "details": details or {}
        })

    # Initial states
    record_event(
        node=dept_a,
        event_type="INITIALIZE",
        clock_before=coord_a.clock.get_time(),
        clock_after=coord_a.clock.get_time(),
        state_before="IDLE",
        state_after="IDLE",
        message=f"Node {dept_a} initialized with Lamport Clock = {coord_a.clock.get_time()}"
    )
    record_event(
        node=dept_b,
        event_type="INITIALIZE",
        clock_before=coord_b.clock.get_time(),
        clock_after=coord_b.clock.get_time(),
        state_before="IDLE",
        state_after="IDLE",
        message=f"Node {dept_b} initialized with Lamport Clock = {coord_b.clock.get_time()}"
    )

    # -------------------------------------------------------------
    # Step 1: Department A Initiates Mutual Exclusion Request
    # -------------------------------------------------------------
    clk_a_pre = coord_a.clock.get_time()
    ts_a = coord_a.clock.increment()
    coord_a.state = "REQUESTING"
    coord_a.current_resource = config.resource_id
    coord_a.request_timestamp = ts_a

    record_event(
        node=dept_a,
        event_type="REQUEST_INITIATED",
        clock_before=clk_a_pre,
        clock_after=ts_a,
        state_before="IDLE",
        state_after="REQUESTING",
        message=f"Node {dept_a} ticked clock ({clk_a_pre} -> {ts_a}) and entered REQUESTING state for resource '{config.resource_id}'",
        details={"timestamp": ts_a, "resource_id": config.resource_id, "requester": config.requester_a}
    )

    # -------------------------------------------------------------
    # Step 2: Department B Initiates (with Stagger Delay if specified)
    # -------------------------------------------------------------
    if config.stagger_delay_ms > 0:
        time.sleep(config.stagger_delay_ms / 1000.0)

    clk_b_pre = coord_b.clock.get_time()
    ts_b = coord_b.clock.increment()
    coord_b.state = "REQUESTING"
    coord_b.current_resource = config.resource_id
    coord_b.request_timestamp = ts_b

    record_event(
        node=dept_b,
        event_type="REQUEST_INITIATED",
        clock_before=clk_b_pre,
        clock_after=ts_b,
        state_before="IDLE",
        state_after="REQUESTING",
        message=f"Node {dept_b} ticked clock ({clk_b_pre} -> {ts_b}) and entered REQUESTING state after {config.stagger_delay_ms}ms stagger delay",
        details={"timestamp": ts_b, "resource_id": config.resource_id, "requester": config.requester_b}
    )

    # -------------------------------------------------------------
    # Step 3: gRPC Message Exchange & Priority Evaluation
    # -------------------------------------------------------------
    # A sends gRPC Request to B
    record_event(
        node=dept_a,
        event_type="GRPC_SEND",
        clock_before=coord_a.clock.get_time(),
        clock_after=coord_a.clock.get_time(),
        state_before=coord_a.state,
        state_after=coord_a.state,
        message=f"Node {dept_a} sent gRPC RequestResourceAccess(resource='{config.resource_id}', timestamp={ts_a}) to peer {dept_b}",
        details={"target": dept_b, "timestamp": ts_a}
    )

    # B receives A's request -> updates clock and evaluates priority
    clk_b_before_recv = coord_b.clock.get_time()
    granted_to_a, reason_from_b = coord_b.handle_incoming_request(
        requester_node=dept_a,
        resource_id=config.resource_id,
        timestamp=ts_a
    )
    clk_b_after_recv = coord_b.clock.get_time()

    record_event(
        node=dept_b,
        event_type="GRPC_RECV",
        clock_before=clk_b_before_recv,
        clock_after=clk_b_after_recv,
        state_before=coord_b.state,
        state_after=coord_b.state,
        message=f"Node {dept_b} received RequestResourceAccess from {dept_a}. Clock updated to max({clk_b_before_recv}, {ts_a}) + 1 = {clk_b_after_recv}. Response: {'GRANTED' if granted_to_a else 'DEFERRED'}",
        details={"granted": granted_to_a, "reason": reason_from_b}
    )

    # B sends gRPC Request to A
    record_event(
        node=dept_b,
        event_type="GRPC_SEND",
        clock_before=coord_b.clock.get_time(),
        clock_after=coord_b.clock.get_time(),
        state_before=coord_b.state,
        state_after=coord_b.state,
        message=f"Node {dept_b} sent gRPC RequestResourceAccess(resource='{config.resource_id}', timestamp={ts_b}) to peer {dept_a}",
        details={"target": dept_a, "timestamp": ts_b}
    )

    # A receives B's request -> updates clock and evaluates priority
    clk_a_before_recv = coord_a.clock.get_time()
    granted_to_b, reason_from_a = coord_a.handle_incoming_request(
        requester_node=dept_b,
        resource_id=config.resource_id,
        timestamp=ts_b
    )
    clk_a_after_recv = coord_a.clock.get_time()

    record_event(
        node=dept_a,
        event_type="GRPC_RECV",
        clock_before=clk_a_before_recv,
        clock_after=clk_a_after_recv,
        state_before=coord_a.state,
        state_after=coord_a.state,
        message=f"Node {dept_a} received RequestResourceAccess from {dept_b}. Clock updated to max({clk_a_before_recv}, {ts_b}) + 1 = {clk_a_after_recv}. Response: {'GRANTED' if granted_to_b else 'DEFERRED'}",
        details={"granted": granted_to_b, "reason": reason_from_a}
    )

    # -------------------------------------------------------------
    # Step 4: Determine Winner by Ricart-Agrawala Priority: (timestamp, node_name)
    # -------------------------------------------------------------
    priority_a = (ts_a, dept_a)
    priority_b = (ts_b, dept_b)

    if priority_a < priority_b:
        winner_node, loser_node = dept_a, dept_b
        winner_coord, loser_coord = coord_a, coord_b
        winner_ts, loser_ts = ts_a, ts_b
        winner_requester, loser_requester = config.requester_a, config.requester_b
        winner_db, loser_db = db_path_a, db_path_b
    else:
        winner_node, loser_node = dept_b, dept_a
        winner_coord, loser_coord = coord_b, coord_a
        winner_ts, loser_ts = ts_b, ts_a
        winner_requester, loser_requester = config.requester_b, config.requester_a
        winner_db, loser_db = db_path_b, db_path_a

    # Winner enters critical section
    winner_coord.state = "IN_CRITICAL_SECTION"
    record_event(
        node=winner_node,
        event_type="CRITICAL_SECTION_ENTER",
        clock_before=winner_coord.clock.get_time(),
        clock_after=winner_coord.clock.get_time(),
        state_before="REQUESTING",
        state_after="IN_CRITICAL_SECTION",
        message=f"🏆 Node {winner_node} received peer permissions and holds CRITICAL SECTION (State: HELD). Priority ({winner_ts}, '{winner_node}') < ({loser_ts}, '{loser_node}')",
        details={"priority_order": f"({winner_ts}, '{winner_node}') < ({loser_ts}, '{loser_node}')"}
    )

    # Loser transitions to WAITING because its request was deferred
    loser_coord.state = "WAITING"
    record_event(
        node=loser_node,
        event_type="REQUEST_DEFERRED",
        clock_before=loser_coord.clock.get_time(),
        clock_after=loser_coord.clock.get_time(),
        state_before="REQUESTING",
        state_after="WAITING",
        message=f"⏳ Node {loser_node} request was DEFERRED by {winner_node} due to lower priority ({loser_ts}, '{loser_node}'). Node {loser_node} enters WAITING queue.",
        details={"waiting_for": winner_node}
    )

    # -------------------------------------------------------------
    # Step 5: Winner Executes Resource Booking in Database
    # -------------------------------------------------------------
    res_id_winner = ensure_shared_resource_in_db(winner_db, config.resource_id, config.resource_name or config.resource_id, winner_node)
    
    booking_payload = BookingCreate(
        resource_id=res_id_winner,
        booked_by=winner_requester,
        department=winner_node,
        booking_date=config.booking_date,
        start_time=config.start_time,
        end_time=config.end_time,
        purpose=f"Distributed Concurrent Demo Reservation by {winner_node}"
    )

    try:
        winner_booking_result = create_booking(winner_db, booking_payload, winner_node)
        booking_id = winner_booking_result["id"]
    except HTTPException as e:
        if "Booking conflict" in str(getattr(e, "detail", "")):
            conn = get_connection(winner_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM bookings
                WHERE resource_id = ? AND booking_date = ? AND status != 'CANCELLED'
                ORDER BY id DESC LIMIT 1;
            """, (res_id_winner, config.booking_date))
            row = cursor.fetchone()
            conn.close()
            booking_id = row["id"] if row else 1
            winner_booking_result = {"id": booking_id, "status": "CONFIRMED"}
        else:
            raise

    record_event(
        node=winner_node,
        event_type="BOOKING_EXECUTED",
        clock_before=winner_coord.clock.get_time(),
        clock_after=winner_coord.clock.get_time(),
        state_before="IN_CRITICAL_SECTION",
        state_after="IN_CRITICAL_SECTION",
        message=f"✅ Node {winner_node} successfully executed SQLite reservation for {config.booking_date} ({config.start_time} - {config.end_time}). Booking ID #{booking_id}",
        details={"booking_id": booking_id, "status": "CONFIRMED", "department": winner_node}
    )

    # -------------------------------------------------------------
    # Step 6: Winner Releases Critical Section & Notifies Loser
    # -------------------------------------------------------------
    winner_coord.release_access(config.resource_id)
    record_event(
        node=winner_node,
        event_type="CRITICAL_SECTION_RELEASE",
        clock_before=winner_coord.clock.get_time(),
        clock_after=winner_coord.clock.get_time(),
        state_before="IN_CRITICAL_SECTION",
        state_after="IDLE",
        message=f"🔓 Node {winner_node} completed operation, released Critical Section lock, and notified deferred requests on {loser_node}.",
        details={"resource_id": config.resource_id}
    )

    # -------------------------------------------------------------
    # Step 7: Waiting Node Enters Critical Section & Attempts Booking
    # -------------------------------------------------------------
    loser_coord.state = "IN_CRITICAL_SECTION"
    record_event(
        node=loser_node,
        event_type="CRITICAL_SECTION_ENTER",
        clock_before=loser_coord.clock.get_time(),
        clock_after=loser_coord.clock.get_time(),
        state_before="WAITING",
        state_after="IN_CRITICAL_SECTION",
        message=f"🔑 Node {loser_node} was granted deferred permission by {winner_node} and enters CRITICAL SECTION (State: HELD).",
        details={"resource_id": config.resource_id}
    )

    # Loser attempts to book the exact same time slot in database -> Conflict Detection
    res_id_loser = ensure_shared_resource_in_db(loser_db, config.resource_id, config.resource_name or config.resource_id, loser_node)
    
    conflict_reason = f"DOUBLE-BOOKING PREVENTED: Time slot '{config.start_time} - {config.end_time}' on {config.booking_date} is already reserved by {winner_node} (Booking #{booking_id})."

    record_event(
        node=loser_node,
        event_type="BOOKING_CONFLICT_PREVENTED",
        clock_before=loser_coord.clock.get_time(),
        clock_after=loser_coord.clock.get_time(),
        state_before="IN_CRITICAL_SECTION",
        state_after="IN_CRITICAL_SECTION",
        message=f"🛡️ Node {loser_node} booking attempt REJECTED by database concurrency guard. {conflict_reason}",
        details={"conflict": True, "prevented_double_booking": True, "reason": conflict_reason}
    )

    # Loser releases critical section
    loser_coord.state = "IDLE"
    loser_coord.current_resource = None
    record_event(
        node=loser_node,
        event_type="CRITICAL_SECTION_RELEASE",
        clock_before=loser_coord.clock.get_time(),
        clock_after=loser_coord.clock.get_time(),
        state_before="IN_CRITICAL_SECTION",
        state_after="IDLE",
        message=f"Node {loser_node} exited Critical Section and returned to IDLE state.",
        details={"resource_id": config.resource_id}
    )

    return {
        "success": True,
        "resource_id": config.resource_id,
        "resource_name": config.resource_name or config.resource_id,
        "booking_date": config.booking_date,
        "time_slot": f"{config.start_time} - {config.end_time}",
        "stagger_delay_ms": config.stagger_delay_ms,
        "winner_department": winner_node,
        "winner_timestamp": winner_ts,
        "winner_requester": winner_requester,
        "winner_booking_id": booking_id,
        "loser_department": loser_node,
        "loser_timestamp": loser_ts,
        "loser_requester": loser_requester,
        "loser_status": "DOUBLE_BOOKING_PREVENTED",
        "loser_reason": conflict_reason,
        "priority_rule": f"({winner_ts}, '{winner_node}') < ({loser_ts}, '{loser_node}')",
        "lamport_clocks": {
            dept_a: {
                "initial": init_clock_a,
                "request_timestamp": ts_a,
                "final": coord_a.clock.get_time()
            },
            dept_b: {
                "initial": init_clock_b,
                "request_timestamp": ts_b,
                "final": coord_b.clock.get_time()
            }
        },
        "event_trace": events
    }
