from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.donor import Donor
from app.models.request import BloodRequest
from app.utils.distance import calculate_distance_kilometers
from app.schemas.request_schema import MatchedDonorOut

# Which blood types can safely donate to which blood type.
# The key is the blood type that needs blood.
# The value is the list of blood types that can give blood to it.
COMPATIBLE_DONOR_TYPES = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}

MAXIMUM_SEARCH_DISTANCE_KILOMETERS = 50
MINIMUM_DAYS_BETWEEN_DONATIONS = 90

# --- AI Smart Donor Matching: scoring weights ------------------------------
# A donor's rank is not just "closest first" -- it blends three signals into
# one match score, the way a real dispatch/triage system would:
#   1. Distance      -- closer donors can respond faster (up to 50 pts, 0 past 50km)
#   2. Compatibility  -- an exact blood-type match is preferred over a cross-type
#                        match (e.g. an O- universal donor), to conserve rare
#                        universal stock for when it's truly needed (30 vs 15 pts)
#   3. Reliability    -- donors with a stronger donation history (points earned
#                        from past donations) are weighted slightly higher (up to 20 pts)
DISTANCE_SCORE_WEIGHT = 50
EXACT_MATCH_SCORE = 30
CROSS_MATCH_SCORE = 15
MAX_RELIABILITY_SCORE = 20
RELIABILITY_POINTS_DIVISOR = 5


def _score_donor(distance_kilometers: float, is_exact_match: bool, donor_points: int) -> float:
    distance_score = max(0.0, DISTANCE_SCORE_WEIGHT - distance_kilometers)
    compatibility_score = EXACT_MATCH_SCORE if is_exact_match else CROSS_MATCH_SCORE
    reliability_score = min(MAX_RELIABILITY_SCORE, donor_points / RELIABILITY_POINTS_DIVISOR)
    return round(distance_score + compatibility_score + reliability_score, 1)


def find_matching_donors(
    db: Session,
    blood_request: BloodRequest,
    maximum_distance_kilometers: float = MAXIMUM_SEARCH_DISTANCE_KILOMETERS,
) -> List[MatchedDonorOut]:
    """
    AI Smart Donor Matching. Finds donors who are compatible with the
    requested blood type, are eligible to donate right now (90+ days
    since their last donation), and are within the search radius --
    then ranks them by a blended match score (distance + compatibility
    + reliability), best match first, instead of just nearest-first.
    """
    compatible_types = COMPATIBLE_DONOR_TYPES.get(blood_request.blood_type_needed, [])
    if not compatible_types:
        return []

    candidate_donors = (
        db.query(Donor)
        .filter(Donor.blood_type.in_(compatible_types))
        .filter(Donor.is_eligible == True)  # noqa: E712
        .all()
    )

    earliest_allowed_last_donation = datetime.utcnow() - timedelta(days=MINIMUM_DAYS_BETWEEN_DONATIONS)

    matches = []
    for donor in candidate_donors:
        if donor.last_donation_date and donor.last_donation_date > earliest_allowed_last_donation:
            continue

        distance = calculate_distance_kilometers(
            blood_request.latitude,
            blood_request.longitude,
            donor.latitude,
            donor.longitude,
        )

        if distance <= maximum_distance_kilometers:
            is_exact_match = donor.blood_type == blood_request.blood_type_needed
            matches.append(
                MatchedDonorOut(
                    donor_id=donor.id,
                    full_name=donor.full_name,
                    blood_type=donor.blood_type,
                    phone_number=donor.phone_number,
                    distance_kilometers=round(distance, 2),
                    points=donor.points,
                    is_exact_match=is_exact_match,
                    match_score=_score_donor(distance, is_exact_match, donor.points),
                    availability_label="Available",
                )
            )

    matches.sort(key=lambda item: item.match_score, reverse=True)
    return matches
