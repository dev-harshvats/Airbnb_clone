"""Account rules: password strength, minimum age and email normalization."""

import re
from datetime import date

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_BYTES = 72  # bcrypt ignores (or rejects) anything beyond this
MIN_AGE_YEARS = 18

_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def password_problem(password: str) -> str | None:
    """Return why a password is unacceptable, or None when it is fine."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        return f"Password must be at most {PASSWORD_MAX_BYTES} bytes long."
    if not _HAS_LETTER.search(password) or not _HAS_DIGIT.search(password):
        return "Password must contain at least one letter and one digit."
    return None


def is_adult(date_of_birth: date, today: date) -> bool:
    birthdays_passed = (today.month, today.day) >= (date_of_birth.month, date_of_birth.day)
    age = today.year - date_of_birth.year - (0 if birthdays_passed else 1)
    return age >= MIN_AGE_YEARS


def normalize_email(email: str) -> str:
    return email.strip().lower()
