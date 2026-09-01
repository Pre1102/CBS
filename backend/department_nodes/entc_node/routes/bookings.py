import os
import sys
from typing import List
from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from backend.department_nodes.common.models import BookingCreate, BookingResponse
    from backend.department_nodes.common.handlers import get_all_bookings, get_booking_by_id, create_booking, cancel_booking
except ImportError:
    from department_nodes.common.models import BookingCreate, BookingResponse
    from department_nodes.common.handlers import get_all_bookings, get_booking_by_id, create_booking, cancel_booking

router = APIRouter()
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "entc.db"))
NODE_DEPT = "E&TC"

@router.get("/bookings", response_model=List[BookingResponse])
def list_bookings():
    return get_all_bookings(DB_PATH)

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int):
    bk = get_booking_by_id(DB_PATH, booking_id)
    if not bk:
        raise HTTPException(status_code=404, detail=f"Booking ID {booking_id} not found in E&TC node")
    return bk

@router.post("/bookings", response_model=BookingResponse, status_code=201)
def add_booking(booking: BookingCreate):
    return create_booking(DB_PATH, booking, NODE_DEPT)

@router.put("/bookings/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking_endpoint(booking_id: int):
    return cancel_booking(DB_PATH, booking_id)
