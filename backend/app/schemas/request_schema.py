from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BloodRequestCreate(BaseModel):
    blood_type_needed: str
    units_needed: int = 1
    patient_name: Optional[str] = None
    urgency_type: str = "emergency"
    urgency_value: Optional[int] = None
    latitude: float
    longitude: float


class BloodRequestOut(BaseModel):
    id: int
    requester_type: str
    requester_id: int
    requester_name: str
    requester_phone: str
    requester_cnic: Optional[str] = None
    requester_address: Optional[str] = None
    blood_type_needed: str
    units_needed: int
    units_fulfilled: int
    units_remaining: int
    patient_name: Optional[str] = None
    urgency_type: str
    urgency_value: Optional[int] = None
    latitude: float
    longitude: float
    status: str
    created_at: datetime


class AcceptRequestInput(BaseModel):
    units_donated: int = 1


class MatchedDonorOut(BaseModel):
    donor_id: int
    full_name: str
    blood_type: str
    phone_number: str
    distance_kilometers: float
    points: int
    is_exact_match: bool = True
    match_score: float = 0.0
    availability_label: str = "Available"
