import os
import tempfile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.department_nodes.common.database import initialize_database
from backend.department_nodes.common.handlers import (
    create_booking, cancel_booking, get_all_bookings, get_booking_by_id
)
from backend.department_nodes.common.models import BookingCreate
from backend.department_nodes.cse_node.routes.resources import router as cse_resources_router
from backend.department_nodes.cse_node.routes.bookings import router as cse_bookings_router

@pytest.fixture
def temp_cse_db():
    """Provides a fresh temporary SQLite database initialized with CSE seed data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_cse.db")
        initialize_database(db_path, "CSE")
        yield db_path

def test_create_booking_success(temp_cse_db):
    booking_in = BookingCreate(
        resource_id=1,
        booked_by="Prof. Smith",
        department="CSE",
        booking_date="2026-10-20",
        start_time="09:00",
        end_time="11:00",
        purpose="Algorithms Lecture"
    )
    result = create_booking(temp_cse_db, booking_in, "CSE")
    assert result["status"] == "CONFIRMED"
    assert result["resource_id"] == 1
    assert result["booked_by"] == "Prof. Smith"

def test_local_booking_conflict_rejected(temp_cse_db):
    """Test that overlapping booking for same resource and date is rejected."""
    b1 = BookingCreate(
        resource_id=1,
        booked_by="Alice",
        department="CSE",
        booking_date="2026-10-25",
        start_time="14:00",
        end_time="16:00",
        purpose="Workshop Part 1"
    )
    create_booking(temp_cse_db, b1, "CSE")

    # Overlapping Booking: 15:00 - 17:00 (overlaps 15:00-16:00)
    b2 = BookingCreate(
        resource_id=1,
        booked_by="Bob",
        department="CSE",
        booking_date="2026-10-25",
        start_time="15:00",
        end_time="17:00",
        purpose="Workshop Part 2"
    )
    with pytest.raises(Exception) as exc_info:
        create_booking(temp_cse_db, b2, "CSE")
    assert "Booking conflict" in str(exc_info.value)

def test_non_overlapping_booking_allowed(temp_cse_db):
    """Test that non-overlapping adjacent time slot is allowed."""
    b1 = BookingCreate(
        resource_id=1,
        booked_by="Alice",
        department="CSE",
        booking_date="2026-10-25",
        start_time="14:00",
        end_time="16:00",
        purpose="Workshop Part 1"
    )
    create_booking(temp_cse_db, b1, "CSE")

    # Adjacent non-overlapping Booking: 16:00 - 18:00
    b2 = BookingCreate(
        resource_id=1,
        booked_by="Charlie",
        department="CSE",
        booking_date="2026-10-25",
        start_time="16:00",
        end_time="18:00",
        purpose="Evening Seminar"
    )
    res2 = create_booking(temp_cse_db, b2, "CSE")
    assert res2["status"] == "CONFIRMED"

def test_invalid_time_range(temp_cse_db):
    b = BookingCreate(
        resource_id=1,
        booked_by="Invalid Time User",
        department="CSE",
        booking_date="2026-10-20",
        start_time="14:00",
        end_time="12:00",  # start > end
        purpose="Invalid Time Test"
    )
    with pytest.raises(Exception) as exc_info:
        create_booking(temp_cse_db, b, "CSE")
    assert "start_time must be strictly before end_time" in str(exc_info.value)

def test_cancel_booking_and_rebooking(temp_cse_db):
    b1 = BookingCreate(
        resource_id=1,
        booked_by="Student Club",
        department="CSE",
        booking_date="2026-11-01",
        start_time="10:00",
        end_time="12:00",
        purpose="Club Meeting"
    )
    create_res = create_booking(temp_cse_db, b1, "CSE")
    booking_id = create_res["id"]

    # Cancel booking
    cancel_res = cancel_booking(temp_cse_db, booking_id)
    assert cancel_res["status"] == "CANCELLED"

    # Re-booking same slot after cancellation must succeed
    rebook_res = create_booking(temp_cse_db, b1, "CSE")
    assert rebook_res["status"] == "CONFIRMED"
