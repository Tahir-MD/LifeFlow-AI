from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hospital import Hospital
from app.models.receiver import Receiver
from app.models.request import BloodRequest
from app.schemas.request_schema import BloodRequestCreate, BloodRequestOut
from app.utils.dependencies import get_current_hospital, get_current_receiver
from app.utils.notify import notify
from app.services.matching_service import find_matching_donors

router = APIRouter(prefix="/requests", tags=["Blood Requests"])


def build_request_out(db: Session, blood_request: BloodRequest) -> BloodRequestOut:
    """
    Fills in who is asking. A hospital request shows the hospital name
    and phone number. A receiver request additionally shows the CNIC
    number and address of the person asking, since they are an
    individual rather than a licensed institution.
    """
    requester_cnic = None
    requester_address = None

    if blood_request.requester_type == "hospital":
        hospital = db.query(Hospital).filter(Hospital.id == blood_request.requester_id).first()
        requester_name = hospital.name if hospital else "Unknown hospital"
        requester_phone = hospital.phone_number if hospital else ""
    else:
        receiver = db.query(Receiver).filter(Receiver.id == blood_request.requester_id).first()
        requester_name = receiver.full_name if receiver else "Unknown receiver"
        requester_phone = receiver.phone_number if receiver else ""
        requester_cnic = receiver.cnic_number if receiver else None
        requester_address = receiver.address if receiver else None

    return BloodRequestOut(
        id=blood_request.id,
        requester_type=blood_request.requester_type,
        requester_id=blood_request.requester_id,
        requester_name=requester_name,
        requester_phone=requester_phone,
        requester_cnic=requester_cnic,
        requester_address=requester_address,
        blood_type_needed=blood_request.blood_type_needed,
        units_needed=blood_request.units_needed,
        units_fulfilled=blood_request.units_fulfilled,
        units_remaining=max(blood_request.units_needed - blood_request.units_fulfilled, 0),
        patient_name=blood_request.patient_name,
        urgency_type=blood_request.urgency_type,
        urgency_value=blood_request.urgency_value,
        latitude=blood_request.latitude,
        longitude=blood_request.longitude,
        status=blood_request.status,
        created_at=blood_request.created_at,
    )


@router.post("/hospital", response_model=BloodRequestOut, status_code=201)
def create_hospital_request(
    request_data: BloodRequestCreate,
    db: Session = Depends(get_db),
    current_hospital: Hospital = Depends(get_current_hospital),
):
    new_request = BloodRequest(
        requester_type="hospital",
        requester_id=current_hospital.id,
        blood_type_needed=request_data.blood_type_needed,
        units_needed=request_data.units_needed,
        patient_name=request_data.patient_name,
        urgency_type=request_data.urgency_type,
        urgency_value=request_data.urgency_value,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    _notify_matching_donors(db, new_request, current_hospital.name)
    return build_request_out(db, new_request)


def _notify_matching_donors(db, blood_request: BloodRequest, requester_name: str) -> None:
    """Tells every compatible nearby donor that a new request just opened."""
    urgency_label = "an emergency" if blood_request.urgency_type == "emergency" else "a scheduled"
    for match in find_matching_donors(db, blood_request):
        notify(
            db, "donor", match.donor_id,
            "New compatible blood request nearby",
            f"{requester_name} needs {blood_request.units_needed} bag(s) of {blood_request.blood_type_needed} "
            f"({urgency_label} request), about {match.distance_kilometers} km away.",
            category="request",
            related_request_id=blood_request.id,
        )
    db.commit()


@router.post("/receiver", response_model=BloodRequestOut, status_code=201)
def create_receiver_request(
    request_data: BloodRequestCreate,
    db: Session = Depends(get_db),
    current_receiver: Receiver = Depends(get_current_receiver),
):
    new_request = BloodRequest(
        requester_type="receiver",
        requester_id=current_receiver.id,
        blood_type_needed=request_data.blood_type_needed,
        units_needed=request_data.units_needed,
        patient_name=request_data.patient_name or current_receiver.patient_name,
        urgency_type=request_data.urgency_type,
        urgency_value=request_data.urgency_value,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    _notify_matching_donors(db, new_request, current_receiver.full_name)
    return build_request_out(db, new_request)


@router.get("", response_model=list[BloodRequestOut])
def list_blood_requests(db: Session = Depends(get_db)):
    requests = db.query(BloodRequest).order_by(BloodRequest.created_at.desc()).all()
    return [build_request_out(db, item) for item in requests]


@router.get("/hospital/history", response_model=list[BloodRequestOut])
def hospital_request_history(
    db: Session = Depends(get_db),
    current_hospital: Hospital = Depends(get_current_hospital),
):
    """
    Every request this hospital has ever sent -- open, closed, or
    still waiting for a donor -- not just the ones a donor has
    fulfilled. This is the hospital's full request history, and it
    stays the same across logins because it is read straight from the
    database by this hospital's id.
    """
    requests = (
        db.query(BloodRequest)
        .filter(BloodRequest.requester_type == "hospital", BloodRequest.requester_id == current_hospital.id)
        .order_by(BloodRequest.created_at.desc())
        .all()
    )
    return [build_request_out(db, item) for item in requests]


@router.get("/receiver/history", response_model=list[BloodRequestOut])
def receiver_request_history(
    db: Session = Depends(get_db),
    current_receiver: Receiver = Depends(get_current_receiver),
):
    """Every request this patient has ever sent -- open, closed, or still waiting."""
    requests = (
        db.query(BloodRequest)
        .filter(BloodRequest.requester_type == "receiver", BloodRequest.requester_id == current_receiver.id)
        .order_by(BloodRequest.created_at.desc())
        .all()
    )
    return [build_request_out(db, item) for item in requests]


@router.get("/{request_id}", response_model=BloodRequestOut)
def get_blood_request(request_id: int, db: Session = Depends(get_db)):
    blood_request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not blood_request:
        raise HTTPException(status_code=404, detail="Request not found")
    return build_request_out(db, blood_request)
