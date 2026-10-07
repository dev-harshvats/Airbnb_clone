import hashlib


def hash_token(raw_token: str) -> str:
    """Refresh tokens are stored only as this digest, so a database leak yields nothing usable."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
