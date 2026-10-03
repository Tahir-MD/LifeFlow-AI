"""
4. AI Chatbot.

A slot-filling assistant: each message the person sends is scanned
for a blood type, a unit count, a hospital name, a contact number,
and an urgency, using the same extraction rules as the report
analyzer (so "Mujhe B+ blood chahiye emergency mein" is understood
just like a pasted report is). Whatever it finds is merged into the
running set of slots the frontend carries between messages; once
every required slot is filled, it tells the frontend the form is
ready to submit -- the person still reviews and submits the actual
request themselves, the chatbot never creates one on its own.
"""
from app.schemas.ai_schema import ChatSlots
from app.services.ai_analyzer_service import (
    extract_blood_type,
    extract_units,
    extract_hospital_name,
    extract_urgency,
    extract_contact_number,
    extract_patient_name,
)

REQUIRED_FIELDS = ["blood_type", "units", "hospital_name", "contact_number"]

FIELD_QUESTIONS = {
    "blood_type": "What blood type is needed? (e.g. B+, O-, AB+)",
    "units": "How many units / bags are needed?",
    "hospital_name": "Which hospital is this for?",
    "contact_number": "What's the best contact number for the donor or hospital to reach you on?",
}

GREETING_KEYWORDS = ["hi", "hello", "salam", "assalam", "hey"]


def _merge_slots(slots: ChatSlots, message: str) -> ChatSlots:
    updated = slots.model_copy()

    found_blood_type = extract_blood_type(message)
    if found_blood_type:
        updated.blood_type = found_blood_type

    found_units = extract_units(message)
    if found_units:
        updated.units = found_units

    found_hospital = extract_hospital_name(message)
    if found_hospital:
        updated.hospital_name = found_hospital

    found_contact = extract_contact_number(message)
    if found_contact:
        updated.contact_number = found_contact

    found_patient_name = extract_patient_name(message)
    if found_patient_name:
        updated.patient_name = found_patient_name

    urgency_type, urgency_value = extract_urgency(message)
    if urgency_type:
        updated.urgency_type = urgency_type
        updated.urgency_value = urgency_value

    return updated


def _missing_fields(slots: ChatSlots):
    return [field for field in REQUIRED_FIELDS if not getattr(slots, field)]


def handle_chat_message(message: str, slots: ChatSlots) -> dict:
    lowered = message.strip().lower()
    updated_slots = _merge_slots(slots, message)
    missing = _missing_fields(updated_slots)

    is_first_message = not any([slots.blood_type, slots.units, slots.hospital_name, slots.contact_number])
    if is_first_message and any(lowered.startswith(g) for g in GREETING_KEYWORDS) and missing == REQUIRED_FIELDS:
        return {
            "reply": (
                "Hi, I'm the LifeFlow assistant. I can help you create an emergency blood request. "
                "What blood type is needed, and how many units?"
            ),
            "slots": updated_slots,
            "ready_to_submit": False,
            "missing_fields": missing,
        }

    if not updated_slots.urgency_type and not missing:
        updated_slots.urgency_type = "emergency"

    if missing:
        acknowledged = []
        if updated_slots.blood_type:
            acknowledged.append(f"blood type {updated_slots.blood_type}")
        if updated_slots.units:
            acknowledged.append(f"{updated_slots.units} unit(s)")
        if updated_slots.hospital_name:
            acknowledged.append(f"at {updated_slots.hospital_name}")

        ack_text = f"Got it — {', '.join(acknowledged)}. " if acknowledged else ""
        next_question = FIELD_QUESTIONS[missing[0]]
        return {
            "reply": f"{ack_text}{next_question}",
            "slots": updated_slots,
            "ready_to_submit": False,
            "missing_fields": missing,
        }

    urgency_phrase = {
        "emergency": "right now, as an emergency",
        "days": f"within {updated_slots.urgency_value} day(s)",
        "months": f"within {updated_slots.urgency_value} month(s)",
    }.get(updated_slots.urgency_type, "as soon as possible")

    summary = (
        f"Here's what I have: {updated_slots.units} unit(s) of {updated_slots.blood_type} "
        f"needed {urgency_phrase} at {updated_slots.hospital_name}, contact {updated_slots.contact_number}. "
        "Please review the request form below and submit it when you're ready."
    )
    return {
        "reply": summary,
        "slots": updated_slots,
        "ready_to_submit": True,
        "missing_fields": [],
    }
