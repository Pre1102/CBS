from enum import Enum
from pydantic import BaseModel, Field

class ResourceType(str, Enum):
    CLASSROOM = "Classroom"
    LABORATORY = "Laboratory"
    SEMINAR_HALL = "Seminar Hall"
    SPORTS_FACILITY = "Sports Facility"
    EQUIPMENT = "Equipment"

class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

# Pydantic Schemas for Resource
class ResourceCreate(BaseModel):
    name: str = Field(..., example="CSE Computer Lab 1")
    resource_type: str = Field(..., example="Laboratory")
    location: str = Field(..., example="CSE Block - Floor 1")
    department: str = Field(..., example="CSE")
    capacity: int = Field(..., gt=0, example=60)
    is_available: bool = True

class ResourceResponse(BaseModel):
    id: int
    name: str
    resource_type: str
    location: str
    department: str
    capacity: int
    is_available: bool

# Pydantic Schemas for Booking
class BookingCreate(BaseModel):
    resource_id: int = Field(..., example=1)
    booked_by: str = Field(..., example="Student")
    department: str = Field(..., example="CSE")
    booking_date: str = Field(..., example="2026-09-15")
    start_time: str = Field(..., example="10:00")
    end_time: str = Field(..., example="12:00")
    purpose: str = Field(..., example="Distributed Systems Lab")

class BookingResponse(BaseModel):
    id: int
    resource_id: int
    booked_by: str
    department: str
    booking_date: str
    start_time: str
    end_time: str
    purpose: str
    status: str
    created_at: str
