import secrets
import string

_ALPHABET = string.ascii_uppercase + string.digits


def generate_booking_code() -> str:
    """A 10-character reservation code, e.g. HMXK4Q2PZ7, that does not reveal booking order."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(10))
