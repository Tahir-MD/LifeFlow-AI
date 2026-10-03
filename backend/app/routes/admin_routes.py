from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin import Admin
from app.models.donor import Donor
from app.models.hospital import Hospital
from app.models.receiver import Receiver
from app.models.request import BloodRequest
from app.models.donation import Donation
from app.models.notification import Notification
from app.models.staff import Staff
from app.models.visitor_log import VisitorEntry
from app.schemas.donor_schema import DonorOut
from app.schemas.hospital_schema import HospitalOut
from app.schemas.receiver_schema import ReceiverOut
from app.schemas.request_schema import BloodRequestOut
from app.schemas.donation_schema import DonationHistoryOut
from app.schemas.notification_schema import NotificationOut
from app.schemas.staff_schema import StaffOut
from app.schemas.visitor_schema import VisitorEntryOut
from app.utils.dependencies import get_current_admin
from app.services.history_service import build_history_entry
from app.services.shortage_service import predict_shortage_for_hospital
from app.schemas.ai_schema import ShortagePredictionOut
from app.routes.request_routes import build_request_out

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Everyone on the platform ---------------------------------------------

@router.get("/donors", response_model=List[DonorOut])
def all_donors(db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    return db.query(Donor).order_by(Donor.created_at.desc()).all()


@router.get("/hospitals", response_model=List[HospitalOut])
def all_hospitals(db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    return db.query(Hospital).order_by(Hospital.created_at.desc()).all()


@router.get("/receivers", response_model=List[ReceiverOut])
def all_receivers(db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    return db.query(Receiver).order_by(Receiver.created_at.desc()).all()


# --- Full history across every user, of every kind -------------------------

@router.get("/requests", response_model=List[BloodRequestOut])
def all_requests(db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    """Every blood request ever made, by every hospital and patient, any status."""
    requests = db.query(BloodRequest).order_by(BloodRequest.created_at.desc()).all()
    return [build_request_out(db, item) for item in requests]


@router.get("/donations", response_model=List[DonationHistoryOut])
def all_donations(db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    """Every completed donation on the platform, from every donor to every hospital/patient."""
    donations = db.query(Donation).order_by(Donation.donated_at.desc()).all()
    results = []
    for donation in donations:
        blood_request = db.query(BloodRequest).filter(BloodRequest.id == donation.request_id).first()
        if not blood_request:
            continue
        entry = build_history_entry(db, donation, blood_request)
        if entry:
            results.append(entry)
    return results


@router.get("/notifications", response_model=List[NotificationOut])
def all_notifications(db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    """Every donor request / message notification sent to anyone, full history."""
    return db.query(Notification).order_by(Notification.created_at.desc()).limit(500).all()


# --- One specific user's own history, as seen from the admin side ---------

@router.get("/donor/{donor_id}/history", response_model=List[DonationHistoryOut])
def donor_history(donor_id: int, db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    donations = (
        db.query(Donation)
        .filter(Donation.donor_id == donor_id)
        .order_by(Donation.donated_at.desc())
        .all()
    )
    results = []
    for donation in donations:
        blood_request = db.query(BloodRequest).filter(BloodRequest.id == donation.request_id).first()
        if not blood_request:
            continue
        entry = build_history_entry(db, donation, blood_request)
        if entry:
            results.append(entry)
    return results


@router.get("/hospital/{hospital_id}/history", response_model=List[BloodRequestOut])
def hospital_history(hospital_id: int, db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    requests = (
        db.query(BloodRequest)
        .filter(BloodRequest.requester_type == "hospital", BloodRequest.requester_id == hospital_id)
        .order_by(BloodRequest.created_at.desc())
        .all()
    )
    return [build_request_out(db, item) for item in requests]


@router.get("/receiver/{receiver_id}/history", response_model=List[BloodRequestOut])
def receiver_history(receiver_id: int, db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    receiver = db.query(Receiver).filter(Receiver.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    requests = (
        db.query(BloodRequest)
        .filter(BloodRequest.requester_type == "receiver", BloodRequest.requester_id == receiver_id)
        .order_by(BloodRequest.created_at.desc())
        .all()
    )
    return [build_request_out(db, item) for item in requests]


# --- Hospital staff and their shift records ---------------------------------

@router.get("/hospital/{hospital_id}/shortage-prediction", response_model=List[ShortagePredictionOut])
def hospital_shortage_prediction(hospital_id: int, db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    """Same AI shortage prediction the hospital itself sees, viewable by the admin for any hospital."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return predict_shortage_for_hospital(db, hospital_id)


@router.get("/staff", response_model=List[StaffOut])
def all_staff(db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    """Every staff login at every hospital, across every shift."""
    return db.query(Staff).order_by(Staff.hospital_id, Staff.shift).all()


@router.get("/staff/{staff_id}/visitors", response_model=List[VisitorEntryOut])
def staff_visitor_history(staff_id: int, db: Session = Depends(get_db), _admin: Admin = Depends(get_current_admin)):
    """One staff member's full shift record -- every donor and patient they logged."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    entries = (
        db.query(VisitorEntry)
        .filter(VisitorEntry.staff_id == staff_id)
        .order_by(VisitorEntry.logged_at.desc())
        .all()
    )
    return [
        VisitorEntryOut(
            id=e.id, staff_id=e.staff_id, hospital_id=e.hospital_id, visitor_type=e.visitor_type,
            full_name=e.full_name, blood_type=e.blood_type, phone_number=e.phone_number,
            from_location=e.from_location, notes=e.notes, logged_at=e.logged_at,
            staff_name=staff.full_name, staff_shift=staff.shift,
        )
        for e in entries
    ]
