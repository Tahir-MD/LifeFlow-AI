"""
3. Blood Shortage Prediction.

For each blood type, this looks at how many bags of that type have
actually been given out against this hospital's requests over the
last 30 days, turns that into an average daily consumption rate, and
projects how many days the current stock will last at that rate.
That, combined with the hospital's own low-stock threshold, decides
the risk band: stable, low, or critical.

This is a transparent statistical projection (a moving-average
depletion model), not a trained ML model -- it needs no historical
training dataset to get started, which matters for a brand-new
hospital account that has no history yet, and it is easy to explain
to a judge or a hospital admin: "at this rate, you have N days left."
"""
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.inventory import BloodInventory
from app.models.request import BloodRequest
from app.models.donation import Donation
from app.schemas.ai_schema import ShortagePredictionOut

BLOOD_TYPES = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
LOOKBACK_DAYS = 30

CRITICAL_DAYS_REMAINING = 3
LOW_DAYS_REMAINING = 7


def _risk_band(units_available: int, low_stock_threshold: int, projected_days_remaining):
    """Combines the raw stock level and the projected days-of-supply into one risk band."""
    critically_low_stock = units_available <= max(1, low_stock_threshold // 2)
    low_on_stock = units_available <= low_stock_threshold

    critically_low_supply = projected_days_remaining is not None and projected_days_remaining <= CRITICAL_DAYS_REMAINING
    low_on_supply = projected_days_remaining is not None and projected_days_remaining <= LOW_DAYS_REMAINING

    if critically_low_stock or critically_low_supply:
        return "critical", "🔴 Critical" if critically_low_stock else "🔴 High shortage risk"
    if low_on_stock or low_on_supply:
        return "low", "🟡 May become low"
    return "stable", "🟢 Stable"


def predict_shortage_for_hospital(db: Session, hospital_id: int) -> List[ShortagePredictionOut]:
    since = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)

    inventory_rows = {
        row.blood_type: row
        for row in db.query(BloodInventory).filter(BloodInventory.hospital_id == hospital_id).all()
    }

    results = []
    for blood_type in BLOOD_TYPES:
        inventory_row = inventory_rows.get(blood_type)
        units_available = inventory_row.units_available if inventory_row else 0
        low_stock_threshold = inventory_row.low_stock_threshold if inventory_row else 5

        units_given_out = (
            db.query(Donation)
            .join(BloodRequest, Donation.request_id == BloodRequest.id)
            .filter(
                BloodRequest.requester_type == "hospital",
                BloodRequest.requester_id == hospital_id,
                BloodRequest.blood_type_needed == blood_type,
                Donation.donated_at >= since,
            )
            .all()
        )
        total_units_given_out = sum(d.units_donated for d in units_given_out)
        avg_daily_consumption = round(total_units_given_out / LOOKBACK_DAYS, 2)

        projected_days_remaining = (
            round(units_available / avg_daily_consumption, 1) if avg_daily_consumption > 0 else None
        )

        risk_level, risk_label = _risk_band(units_available, low_stock_threshold, projected_days_remaining)

        results.append(ShortagePredictionOut(
            blood_type=blood_type,
            units_available=units_available,
            low_stock_threshold=low_stock_threshold,
            avg_daily_consumption=avg_daily_consumption,
            projected_days_remaining=projected_days_remaining,
            risk_level=risk_level,
            risk_label=risk_label,
        ))

    # Most urgent first, so the riskiest blood types are what the hospital sees right away.
    order = {"critical": 0, "low": 1, "stable": 2}
    results.sort(key=lambda r: (order[r.risk_level], r.units_available))
    return results
