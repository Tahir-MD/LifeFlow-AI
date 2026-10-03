from pydantic import BaseModel
from typing import Optional, List, Dict


# ---- 1. AI Request Analyzer ------------------------------------------------

class ReportAnalysisRequest(BaseModel):
    report_text: str


class ReportAnalysisResult(BaseModel):
    blood_type: Optional[str] = None
    units: Optional[int] = None
    hospital_name: Optional[str] = None
    urgency_type: Optional[str] = None  # "emergency" | "days" | "months"
    urgency_value: Optional[int] = None
    patient_name: Optional[str] = None
    confidence: float = 0.0
    fields_found: List[str] = []
    notes: str = ""


# ---- 3. Blood Shortage Prediction ------------------------------------------

class ShortagePredictionOut(BaseModel):
    blood_type: str
    units_available: int
    low_stock_threshold: int
    avg_daily_consumption: float
    projected_days_remaining: Optional[float] = None
    risk_level: str  # "stable" | "low" | "critical"
    risk_label: str  # "🟢 Stable" | "🟡 May become low" | "🔴 High shortage risk" / "🔴 Critical"


# ---- 4. AI Chatbot ----------------------------------------------------------

class ChatSlots(BaseModel):
    blood_type: Optional[str] = None
    units: Optional[int] = None
    hospital_name: Optional[str] = None
    contact_number: Optional[str] = None
    urgency_type: Optional[str] = None
    urgency_value: Optional[int] = None
    patient_name: Optional[str] = None


class ChatMessageIn(BaseModel):
    message: str
    slots: Optional[ChatSlots] = None


class ChatReplyOut(BaseModel):
    reply: str
    slots: ChatSlots
    ready_to_submit: bool = False
    missing_fields: List[str] = []
