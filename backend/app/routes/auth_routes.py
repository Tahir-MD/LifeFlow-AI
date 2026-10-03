from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donor import Donor
from app.models.hospital import Hospital
from app.models.receiver import Receiver
from app.models.admin import Admin
from app.models.staff import Staff
from app.schemas.donor_schema import DonorCreate, DonorOut, DonorLogin
from app.schemas.hospital_schema import HospitalCreate, HospitalOut, HospitalLogin
from app.schemas.receiver_schema import ReceiverCreate, ReceiverOut, ReceiverLogin
from app.schemas.admin_schema import AdminLogin, AdminChangePassword
from app.schemas.staff_schema import StaffLogin
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/donor", response_model=DonorOut, status_code=status.HTTP_201_CREATED)
def register_donor(donor_data: DonorCreate, db: Session = Depends(get_db)):
    existing = db.query(Donor).filter(Donor.email == donor_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    new_donor = Donor(
        full_name=donor_data.full_name,
        email=donor_data.email,
        hashed_password=hash_password(donor_data.password),
        blood_type=donor_data.blood_type,
        phone_number=donor_data.phone_number,
        latitude=donor_data.latitude,
        longitude=donor_data.longitude,
    )
    db.add(new_donor)
    db.commit()
    db.refresh(new_donor)
    return new_donor


@router.post("/register/hospital", response_model=HospitalOut, status_code=status.HTTP_201_CREATED)
def register_hospital(hospital_data: HospitalCreate, db: Session = Depends(get_db)):
    existing = db.query(Hospital).filter(Hospital.email == hospital_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    new_hospital = Hospital(
        name=hospital_data.name,
        email=hospital_data.email,
        hashed_password=hash_password(hospital_data.password),
        license_number=hospital_data.license_number,
        phone_number=hospital_data.phone_number,
        latitude=hospital_data.latitude,
        longitude=hospital_data.longitude,
    )
    db.add(new_hospital)
    db.commit()
    db.refresh(new_hospital)
    return new_hospital


@router.post("/register/receiver", response_model=ReceiverOut, status_code=status.HTTP_201_CREATED)
def register_receiver(receiver_data: ReceiverCreate, db: Session = Depends(get_db)):
    existing = db.query(Receiver).filter(Receiver.email == receiver_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    new_receiver = Receiver(
        full_name=receiver_data.full_name,
        email=receiver_data.email,
        hashed_password=hash_password(receiver_data.password),
        phone_number=receiver_data.phone_number,
        cnic_number=receiver_data.cnic_number,
        address=receiver_data.address,
        patient_name=receiver_data.patient_name,
        latitude=receiver_data.latitude,
        longitude=receiver_data.longitude,
    )
    db.add(new_receiver)
    db.commit()
    db.refresh(new_receiver)
    return new_receiver


@router.post("/login/donor")
def login_donor(login_data: DonorLogin, db: Session = Depends(get_db)):
    donor = db.query(Donor).filter(Donor.email == login_data.email).first()
    if not donor or not verify_password(login_data.password, donor.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(donor.id), "role": "donor"})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login/hospital")
def login_hospital(login_data: HospitalLogin, db: Session = Depends(get_db)):
    hospital = db.query(Hospital).filter(Hospital.email == login_data.email).first()
    if not hospital or not verify_password(login_data.password, hospital.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(hospital.id), "role": "hospital"})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login/receiver")
def login_receiver(login_data: ReceiverLogin, db: Session = Depends(get_db)):
    receiver = db.query(Receiver).filter(Receiver.email == login_data.email).first()
    if not receiver or not verify_password(login_data.password, receiver.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(receiver.id), "role": "receiver"})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login/admin")
def login_admin(login_data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == login_data.email).first()
    if not admin or not verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(admin.id), "role": "admin"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "must_change_password": admin.must_change_password,
    }


@router.post("/admin/change-password")
def change_admin_password(
    payload: AdminChangePassword,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    if not verify_password(payload.current_password, current_admin.hashed_password):
        raise HTTPException(status_code=401, detail="Your current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=400, detail="New password must be different from the current one")

    current_admin.hashed_password = hash_password(payload.new_password)
    current_admin.must_change_password = False
    db.commit()
    return {"message": "Password updated. You can now use the dashboard."}


@router.post("/login/staff")
def login_staff(login_data: StaffLogin, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(Staff.email == login_data.email).first()
    if not staff or not verify_password(login_data.password, staff.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(staff.id), "role": "staff"})
    return {"access_token": token, "token_type": "bearer"}
