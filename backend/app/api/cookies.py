from fastapi import Response

from app.core.config import Settings
from app.domain.entities import AuthSession

REFRESH_COOKIE = "refresh_token"
# Scoped to the auth endpoints, so the browser never sends the refresh token anywhere else.
REFRESH_COOKIE_PATH = "/api/v1/auth"


def set_refresh_cookie(response: Response, session: AuthSession, settings: Settings) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        session.refresh_token,
        max_age=int(settings.refresh_ttl.total_seconds()),
        path=REFRESH_COOKIE_PATH,
        httponly=True,  # not readable by JavaScript, so XSS cannot steal it
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
