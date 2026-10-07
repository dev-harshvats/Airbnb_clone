import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.domain.errors import DomainError, ErrorKind
from app.ports.clock import Clock
from app.ports.security import IssuedToken, TokenClaims, TokenType

ALGORITHM = "HS256"
_REQUIRED_CLAIMS = ["sub", "type", "jti", "iat", "exp"]


def _invalid() -> DomainError:
    return DomainError(
        ErrorKind.UNAUTHENTICATED, "INVALID_TOKEN", "Your session is invalid or has expired."
    )


class JwtCodec:
    """Signs and verifies tokens. Time comes from the injected Clock, never the wall clock."""

    def __init__(
        self, secret: str, access_ttl: timedelta, refresh_ttl: timedelta, clock: Clock
    ) -> None:
        self._secret = secret
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl
        self._clock = clock

    def create_access_token(self, user_id: int) -> IssuedToken:
        return self._issue(user_id, "access", self._access_ttl)

    def create_refresh_token(self, user_id: int, family_id: str) -> IssuedToken:
        return self._issue(user_id, "refresh", self._refresh_ttl, {"fam": family_id})

    def decode_token(self, token: str, expected_type: TokenType) -> TokenClaims:
        try:
            # Only HS256 is accepted (blocks "alg: none" and algorithm-confusion attacks).
            # Expiry is checked below against the injected clock, not the wall clock.
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": _REQUIRED_CLAIMS, "verify_exp": False, "verify_iat": False},
            )
            user_id = int(claims["sub"])
            issued_at = datetime.fromtimestamp(claims["iat"], UTC)
            expires_at = datetime.fromtimestamp(claims["exp"], UTC)
        except (jwt.PyJWTError, ValueError, TypeError, OverflowError, OSError) as exc:
            raise _invalid() from exc

        if claims["type"] != expected_type or expires_at <= self._clock.now():
            raise _invalid()
        family_id = claims.get("fam")
        if expected_type == "refresh" and not isinstance(family_id, str):
            raise _invalid()
        return TokenClaims(user_id, expected_type, claims["jti"], family_id, issued_at, expires_at)

    def _issue(
        self, user_id: int, token_type: TokenType, ttl: timedelta, extra: dict | None = None
    ) -> IssuedToken:
        issued_at = self._clock.now().replace(microsecond=0)  # JWT times are whole seconds
        expires_at = issued_at + ttl
        jti = uuid.uuid4().hex
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "jti": jti,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        } | (extra or {})
        return IssuedToken(jwt.encode(payload, self._secret, algorithm=ALGORITHM), jti, expires_at)
