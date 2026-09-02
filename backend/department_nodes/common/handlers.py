import datetime
import sqlite3
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from backend.department_nodes.common.database import get_connection
from backend.department_nodes.common.models import ResourceCreate, BookingCreate

def get_all_resources(db_path: str) -> List[Dict[str, Any]]:
    """
    Retrieve all resources from node SQLite database.
    Dynamically computes is_available based on active CONFIRMED bookings.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resources;")
    rows = cursor.fetchall()
    
    resources = []
    for row in rows:
        r = dict(row)
        # Check if there are active bookings for this resource
        cursor.execute("""
            SELECT COUNT(*) as count FROM bookings
            WHERE resource_id = ? AND status = 'CONFIRMED';
        """, (r["id"],))
        b_count = cursor.fetchone()["count"]
        # Resource is available if no active CONFIRMED booking is blocking it
        r["is_available"] = True if b_count == 0 else False
        resources.append(r)
        
    conn.close()
    return resources


def get_resource_by_id(db_path: str, resource_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve resource by ID from node SQLite database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resources WHERE id = ?;", (resource_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_resource(db_path: str, resource: ResourceCreate, node_dept: str) -> Dict[str, Any]:
    """Create new resource with department ownership validation."""
    if resource.department.upper() != node_dept.upper():
        raise HTTPException(
            status_code=400,
            detail=f"Department mismatch: {node_dept} node cannot create resources for '{resource.department}'"
        )
    
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check if resource with same name and department already exists
    cursor.execute("SELECT * FROM resources WHERE name = ? AND department = ?;", (resource.name, resource.department))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return dict(existing)

    cursor.execute("""
        INSERT OR IGNORE INTO resources (name, resource_type, location, department, capacity, is_available)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (
        resource.name,
        resource.resource_type,
        resource.location,
        resource.department,
        resource.capacity,
        1 if resource.is_available else 0
    ))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.execute("SELECT * FROM resources WHERE id = ?;", (new_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else dict(existing) if existing else {}


def get_all_bookings(db_path: str) -> List[Dict[str, Any]]:
    """Retrieve all bookings from node SQLite database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_booking_by_id(db_path: str, booking_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve booking by ID from node SQLite database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?;", (booking_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def has_booking_conflict(db_path: str, resource_id: int, booking_date: str, start_time: str, end_time: str) -> bool:
    """
    Local Conflict Check:
    Checks for overlapping active (CONFIRMED) bookings for the same resource on the given date.
    Overlap condition: new_start < existing_end AND new_end > existing_start
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start_time, end_time FROM bookings
        WHERE resource_id = ? AND booking_date = ? AND status != 'CANCELLED';
    """, (resource_id, booking_date))
    existing_bookings = cursor.fetchall()
    conn.close()

    for row in existing_bookings:
        exist_start = row["start_time"]
        exist_end = row["end_time"]
        
        # Check time overlap
        if start_time < exist_end and end_time > exist_start:
            return True

    return False

def create_booking(db_path: str, booking: BookingCreate, node_dept: str) -> Dict[str, Any]:
    """
    Create a new booking with local conflict and ownership validation.
    """
    # 1. Validate start_time < end_time
    if booking.start_time >= booking.end_time:
        raise HTTPException(
            status_code=400,
            detail="Invalid booking time: start_time must be strictly before end_time"
        )

    # 2. Check if resource exists locally
    res = get_resource_by_id(db_path, booking.resource_id)
    if not res:
        raise HTTPException(
            status_code=404,
            detail=f"Resource ID {booking.resource_id} not found in {node_dept} node"
        )

    # 3. Check department ownership
    if res["department"].upper() != node_dept.upper():
        raise HTTPException(
            status_code=400,
            detail=f"Resource ID {booking.resource_id} belongs to {res['department']}, not {node_dept}"
        )

    # 4. Local conflict detection
    if has_booking_conflict(db_path, booking.resource_id, booking.booking_date, booking.start_time, booking.end_time):
        raise HTTPException(
            status_code=400,
            detail=f"Booking conflict: Resource ID {booking.resource_id} already has an overlapping booking for {booking.booking_date} ({booking.start_time} - {booking.end_time})"
        )

    # 5. Insert new booking
    conn = get_connection(db_path)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO bookings (resource_id, booked_by, department, booking_date, start_time, end_time, purpose, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?);
    """, (
        booking.resource_id,
        booking.booked_by,
        booking.department,
        booking.booking_date,
        booking.start_time,
        booking.end_time,
        booking.purpose,
        created_at
    ))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.execute("SELECT * FROM bookings WHERE id = ?;", (new_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def cancel_booking(db_path: str, booking_id: int) -> Dict[str, Any]:
    """
    Delete an existing booking from the node SQLite database.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?;", (booking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Booking ID {booking_id} not found")

    cursor.execute("DELETE FROM bookings WHERE id = ?;", (booking_id,))
    conn.commit()
    conn.close()
    deleted_booking = dict(row)
    deleted_booking["status"] = "CANCELLED"
    return deleted_booking
