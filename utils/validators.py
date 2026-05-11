# =============================================================
# utils/validators.py — Studyverse Café | Input Validation
# =============================================================
# All user input MUST be validated before touching the DB.
# These helpers return (is_valid: bool, error_message: str).
# Routes call these before running any SQL.
# =============================================================

import re
from datetime import datetime, date


# ── Constants ────────────────────────────────────────────────

VALID_ZONES = [
    "Silent Hall",
    "Midnight Corner",
    "Reader's Lounge",
    "Solo Study Booth",
    "Creator Workspace",
]

VALID_PLANS = [
    "Daily Pass",
    "Weekly Pass",
    "Monthly Member",
]


# ── Helpers ──────────────────────────────────────────────────

def is_valid_email(email: str) -> bool:
    """Simple regex check for email format."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return bool(re.match(pattern, email.strip()))


def is_valid_phone(phone: str) -> bool:
    """
    Accepts Indian mobile numbers:
    +91 98765 43210 / 9876543210 / 098765 43210
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    pattern = r"^(\+91)?[6-9]\d{9}$"
    return bool(re.match(pattern, cleaned))


def is_future_date(date_str: str) -> bool:
    """Returns True if date_str (YYYY-MM-DD) is today or in the future."""
    try:
        visit = datetime.strptime(date_str, "%Y-%m-%d").date()
        return visit >= date.today()
    except ValueError:
        return False


# ── Reservation Validator ────────────────────────────────────

def validate_reservation(data: dict) -> tuple[bool, str]:
    """
    Validates all fields for a new reservation.

    Returns:
        (True, "")           — all good
        (False, "reason")    — validation failed
    """
    required = ["full_name", "phone", "visit_date", "arrival_time", "zone", "plan"]
    for field in required:
        if not data.get(field, "").strip():
            return False, f"'{field}' is required."

    if len(data["full_name"].strip()) < 2:
        return False, "Name must be at least 2 characters."

    if not is_valid_phone(data["phone"]):
        return False, "Invalid phone number. Use a valid Indian mobile number."

    if data.get("email") and not is_valid_email(data["email"]):
        return False, "Invalid email address."

    if not is_future_date(data["visit_date"]):
        return False, "Visit date must be today or in the future."

    if data["zone"] not in VALID_ZONES:
        return False, f"Invalid zone. Choose from: {', '.join(VALID_ZONES)}"

    if data["plan"] not in VALID_PLANS:
        return False, f"Invalid plan. Choose from: {', '.join(VALID_PLANS)}"

    return True, ""


# ── Membership Validator ─────────────────────────────────────

def validate_membership(data: dict) -> tuple[bool, str]:
    """Validates a new membership purchase."""
    required = ["full_name", "phone", "email", "plan", "start_date"]
    for field in required:
        if not data.get(field, "").strip():
            return False, f"'{field}' is required."

    if not is_valid_phone(data["phone"]):
        return False, "Invalid phone number."

    if not is_valid_email(data["email"]):
        return False, "Invalid email address."

    if data["plan"] not in VALID_PLANS:
        return False, f"Invalid plan. Choose from: {', '.join(VALID_PLANS)}"

    if not is_future_date(data["start_date"]):
        return False, "Start date must be today or in the future."

    return True, ""


# ── Contact Validator ────────────────────────────────────────

def validate_contact(data: dict) -> tuple[bool, str]:
    """Validates a contact form submission."""
    required = ["name", "email", "message"]
    for field in required:
        if not data.get(field, "").strip():
            return False, f"'{field}' is required."

    if not is_valid_email(data["email"]):
        return False, "Invalid email address."

    if len(data["message"].strip()) < 10:
        return False, "Message must be at least 10 characters."

    return True, ""
