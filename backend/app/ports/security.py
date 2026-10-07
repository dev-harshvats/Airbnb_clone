from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

TokenType = Literal["access", "refresh"]


@dataclass(frozen=True, slots=True)
class IssuedToken:
    token: str
    jti: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: int
    token_type: TokenType
    jti: str
    family_id: str | None
    issued_at: datetime
    expires_at: datetime


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, hashed: str | None) -> bool:
        """Check a password. With `hashed=None` it still does equivalent work and returns
        False, so callers can treat "no such user" and "wrong password" identically."""


class TokenCodec(Protocol):
    def create_access_token(self, user_id: int) -> IssuedToken: ...

    def create_refresh_token(self, user_id: int, family_id: str) -> IssuedToken: ...

    def decode_token(self, token: str, expected_type: TokenType) -> TokenClaims:
        """Raise DomainError(UNAUTHENTICATED, "INVALID_TOKEN") for any bad, forged,
        expired or wrong-type token."""
