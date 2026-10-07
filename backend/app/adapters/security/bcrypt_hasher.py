from functools import cache

import bcrypt


@cache
def _decoy_hash(rounds: int) -> bytes:
    """A real hash to compare against when no account exists, so timing does not reveal it."""
    return bcrypt.hashpw(b"decoy-password-for-timing", bcrypt.gensalt(rounds))


class BcryptHasher:
    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(self._rounds)).decode("ascii")

    def verify(self, password: str, hashed: str | None) -> bool:
        target = hashed.encode("ascii") if hashed else _decoy_hash(self._rounds)
        try:
            matches = bcrypt.checkpw(password.encode("utf-8"), target)
        except ValueError:  # bcrypt refuses passwords over 72 bytes; they cannot match anything
            return False
        return matches and hashed is not None
