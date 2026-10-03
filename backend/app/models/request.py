from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from app.database import Base


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(Integer, primary_key=True, index=True)

    # requester_type is either "hospital" or "receiver".
    # requester_id points to the id of that hospital or that receiver.
    requester_type = Column(String, nullable=False)
    requester_id = Column(Integer, nullable=False)

    blood_type_needed = Column(String, nullable=False)
    units_needed = Column(Integer, default=1)
    units_fulfilled = Column(Integer, default=0)
    patient_name = Column(String, nullable=True)

    # urgency_type is one of "emergency", "days", or "months".
    # urgency_value holds the number of days or months, and is empty for emergency.
    urgency_type = Column(String, default="emergency")
    urgency_value = Column(Integer, nullable=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
