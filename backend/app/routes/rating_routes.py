from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donation import Donation
from app.models.request import BloodRequest
from app.models.rating import Rating
from app.models.donor import Donor
from app.schemas.rating_schema import RatingCreate, RatingOut, RatingSummaryOut
from app.utils.dependencies import get_current_donor, get_current_requester
from app.utils.notify import notify

router = APIRouter(prefix="/ratings", tags=["Ratings"])


def _get_donation_or_404(db: Session, donation_id: int) -> Donation:
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation


@router.post("/{donation_id}/rate-donor", response_model=RatingOut, status_code=201)
def rate_donor(
    donation_id: int,
    rating_data: RatingCreate,
    db: Session = Depends(get_db),
    requester=Depends(get_current_requester),
):
    """Called by the hospital or patient who received blood, to rate the donor who gave it."""
    role, account = requester
    donation = _get_donation_or_404(db, donation_id)
    blood_request = db.query(BloodRequest).filter(BloodRequest.id == donation.request_id).first()
    if not blood_request or blood_request.requester_type != role or blood_request.requester_id != account.id:
        raise HTTPException(status_code=403, detail="This donation was not made against one of your requests")

    new_rating = Rating(
        donation_id=donation_id,
        direction="requester_to_donor",
        stars=rating_data.stars,
        comment=rating_data.comment,
    )
    db.add(new_rating)

    donor = db.query(Donor).filter(Donor.id == donation.donor_id).first()
    if donor:
        notify(db, "donor", donor.id, "You received a new rating",
               f"You were rated {rating_data.stars} out of 5 stars for a recent donation.",
               category="donation")

    db.commit()
    db.refresh(new_rating)
    return new_rating


@router.post("/{donation_id}/rate-requester", response_model=RatingOut, status_code=201)
def rate_requester(
    donation_id: int,
    rating_data: RatingCreate,
    db: Session = Depends(get_db),
    current_donor: Donor = Depends(get_current_donor),
):
    """Called by the donor, to rate the hospital or patient they gave blood to."""
    donation = _get_donation_or_404(db, donation_id)
    if donation.donor_id != current_donor.id:
        raise HTTPException(status_code=403, detail="This is not one of your donations")

    new_rating = Rating(
        donation_id=donation_id,
        direction="donor_to_requester",
        stars=rating_data.stars,
        comment=rating_data.comment,
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating


@router.get("/donor/{donor_id}", response_model=RatingSummaryOut)
def get_donor_ratings(donor_id: int, db: Session = Depends(get_db)):
    """Public reputation view: what requesters have said about this donor."""
    donation_ids = [d.id for d in db.query(Donation.id).filter(Donation.donor_id == donor_id).all()]
    ratings = (
        db.query(Rating)
        .filter(Rating.donation_id.in_(donation_ids), Rating.direction == "requester_to_donor")
        .order_by(Rating.created_at.desc())
        .all()
        if donation_ids else []
    )
    average = round(sum(r.stars for r in ratings) / len(ratings), 2) if ratings else None
    return RatingSummaryOut(average_stars=average, total_ratings=len(ratings), ratings=ratings)
