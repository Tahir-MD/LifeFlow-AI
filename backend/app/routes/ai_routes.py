from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hospital import Hospital
from app.schemas.ai_schema import (
    ReportAnalysisRequest,
    ReportAnalysisResult,
    ShortagePredictionOut,
    ChatMessageIn,
    ChatReplyOut,
    ChatSlots,
)
from app.services.ai_analyzer_service import analyze_report_text
from app.services.shortage_service import predict_shortage_for_hospital
from app.services.chatbot_service import handle_chat_message
from app.utils.dependencies import get_current_hospital

router = APIRouter(prefix="/ai", tags=["AI Features"])


# ---- 1. AI Request Analyzer -------------------------------------------------

@router.post("/analyze-report", response_model=ReportAnalysisResult)
def analyze_report(payload: ReportAnalysisRequest):
    """
    Reads a pasted prescription/report/referral text and pulls out
    the blood type, units needed, hospital name, patient name, and
    urgency. Nothing is saved -- the caller reviews the result and
    fills in / submits the actual request themselves.
    """
    extracted = analyze_report_text(payload.report_text)

    fields_found = [key for key in ("blood_type", "units", "hospital_name", "urgency_type") if extracted.get(key)]
    confidence = round(len(fields_found) / 4, 2)

    notes = (
        "Extracted using a real language model." if extracted.get("source") == "llm"
        else "Extracted using LifeFlow's built-in rules (no blood type, unit count, hospital "
             "name, or urgency phrase found is simply left blank for you to fill in)."
    )

    return ReportAnalysisResult(
        blood_type=extracted.get("blood_type"),
        units=extracted.get("units"),
        hospital_name=extracted.get("hospital_name"),
        urgency_type=extracted.get("urgency_type"),
        urgency_value=extracted.get("urgency_value"),
        patient_name=extracted.get("patient_name"),
        confidence=confidence,
        fields_found=fields_found,
        notes=notes,
    )


# ---- 3. Blood Shortage Prediction ------------------------------------------

@router.get("/shortage-prediction", response_model=list[ShortagePredictionOut])
def shortage_prediction(db: Session = Depends(get_db), current_hospital: Hospital = Depends(get_current_hospital)):
    """Per-blood-type shortage risk for the logged-in hospital, based on its own usage history."""
    return predict_shortage_for_hospital(db, current_hospital.id)


# ---- 4. AI Chatbot -----------------------------------------------------------

@router.post("/chat", response_model=ChatReplyOut)
def chat(payload: ChatMessageIn):
    """
    One turn of the guided blood-request chatbot. The frontend sends
    the message plus whatever slots it has collected so far; this
    returns the assistant's reply and the updated slots. No login
    required -- this never creates a request by itself.
    """
    slots = payload.slots or ChatSlots()
    result = handle_chat_message(payload.message, slots)
    return ChatReplyOut(**result)
