"""
1. AI Request Analyzer -- and the extraction engine the chatbot (4)
also reuses to read what a person typed.

This is a lightweight, fully offline rule-based text analyzer:
regex and keyword matching, not a vision model or an LLM, so a
patient's prescription or report has to be typed or pasted as text
(photo OCR would need an external vision API, which this project
does not depend on to run). If GROQ_API_KEY is set (see
llm_client.py), free-text understanding is upgraded to a real model
automatically; otherwise these rules are used, and they cover the
common phrasings well enough for a working demo.
"""
import re
from typing import Optional, Tuple

from app.services.llm_client import call_llm_json

VALID_BLOOD_TYPES = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]

_BLOOD_TYPE_PATTERN = re.compile(r"(?<![A-Za-z])(AB|A|B|O)\s?([+\-])(?![A-Za-z0-9])", re.IGNORECASE)

_UNITS_PATTERN = re.compile(
    r"(\d{1,2})\s*(?:units?|bags?|pints?|bottles?)",
    re.IGNORECASE,
)

# Matches a run of Capitalized Words ending in "Hospital" / "Medical Center" /
# etc, e.g. "City General Hospital" -- but not a whole sentence that merely
# happens to contain one, like "Please arrange at City General Hospital".
_HOSPITAL_PATTERN = re.compile(
    r"\b((?:[A-Z][A-Za-z'.&\-]*\s+){0,4}(?:Hospital|Medical Center|Medical Centre|Clinic|Trust))\b",
)

_CRITICAL_KEYWORDS = [
    "critical", "emergency", "urgent", "asap", "immediately", "stat",
    "zaroorat", "zarurat", "abhi", "foran",
]

_DAYS_PATTERN = re.compile(r"within\s+(\d{1,2})\s*days?", re.IGNORECASE)
_MONTHS_PATTERN = re.compile(r"within\s+(\d{1,2})\s*months?", re.IGNORECASE)

_PATIENT_NAME_PATTERN = re.compile(
    r"patient(?:'s)?\s*name\s*[:\-]?\s*([A-Za-z][A-Za-z .]{1,40})", re.IGNORECASE
)


def extract_blood_type(text: str) -> Optional[str]:
    match = _BLOOD_TYPE_PATTERN.search(text)
    if not match:
        return None
    candidate = f"{match.group(1).upper()}{match.group(2)}"
    return candidate if candidate in VALID_BLOOD_TYPES else None


def extract_units(text: str) -> Optional[int]:
    match = _UNITS_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return None


def extract_hospital_name(text: str) -> Optional[str]:
    match = _HOSPITAL_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def extract_patient_name(text: str) -> Optional[str]:
    match = _PATIENT_NAME_PATTERN.search(text)
    if match:
        return match.group(1).strip().rstrip(".")
    return None


def extract_urgency(text: str) -> Tuple[Optional[str], Optional[int]]:
    lowered = text.lower()

    if any(keyword in lowered for keyword in _CRITICAL_KEYWORDS):
        return "emergency", None

    days_match = _DAYS_PATTERN.search(text)
    if days_match:
        return "days", int(days_match.group(1))

    months_match = _MONTHS_PATTERN.search(text)
    if months_match:
        return "months", int(months_match.group(1))

    return None, None


def extract_contact_number(text: str) -> Optional[str]:
    match = re.search(r"(\+?\d[\d\- ]{8,14}\d)", text)
    return match.group(1).strip() if match else None


_ANALYZER_SYSTEM_PROMPT = (
    "You extract structured blood-request fields from a patient's report or "
    "prescription text. Reply with ONLY a JSON object with these keys: "
    "blood_type (one of O-,O+,A-,A+,B-,B+,AB-,AB+ or null), units (integer or null), "
    "hospital_name (string or null), urgency_type (one of 'emergency','days','months' or null), "
    "urgency_value (integer, the number of days/months, or null), "
    "patient_name (string or null). No prose, no markdown, just the JSON object."
)


def analyze_report_text(text: str) -> dict:
    """
    Pulls out blood_type, units, hospital_name, urgency, and
    patient_name from free text. Tries a real LLM first if one is
    configured (see llm_client.py); always falls back to the regex
    rules below, which run instantly and need no external call.
    """
    llm_result = call_llm_json(_ANALYZER_SYSTEM_PROMPT, text)
    if llm_result and isinstance(llm_result, dict):
        blood_type = llm_result.get("blood_type")
        if blood_type not in VALID_BLOOD_TYPES:
            blood_type = extract_blood_type(text)
        return {
            "blood_type": blood_type,
            "units": llm_result.get("units") or extract_units(text),
            "hospital_name": llm_result.get("hospital_name") or extract_hospital_name(text),
            "urgency_type": llm_result.get("urgency_type"),
            "urgency_value": llm_result.get("urgency_value"),
            "patient_name": llm_result.get("patient_name") or extract_patient_name(text),
            "source": "llm",
        }

    urgency_type, urgency_value = extract_urgency(text)
    return {
        "blood_type": extract_blood_type(text),
        "units": extract_units(text),
        "hospital_name": extract_hospital_name(text),
        "urgency_type": urgency_type,
        "urgency_value": urgency_value,
        "patient_name": extract_patient_name(text),
        "source": "rules",
    }
