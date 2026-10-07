"""Per-client-IP rate limiting for credential endpoints (SRS AUTH-6)."""

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import Settings
from app.core.errors import error_response
from app.core.http import client_ip

# In-memory counters: correct for the single-process deployment in the design doc. A multi-node
# deployment would point `storage_uri` at Redis.
limiter = Limiter(key_func=client_ip, storage_uri="memory://")

# The decorators below run at import time, before settings exist, so they take these callables and
# the limits are resolved on every request from whatever the running app was configured with.
_limits = {
    "auth": Settings.model_fields["AUTH_RATE_LIMIT"].default,
    "lookup": Settings.model_fields["LOOKUP_RATE_LIMIT"].default,
}


def auth_limit() -> str:
    """Login and signup attempts."""
    return _limits["auth"]


def lookup_limit() -> str:
    """Email existence checks."""
    return _limits["lookup"]


async def _handle_rate_limited(_: Request, __: RateLimitExceeded):
    response = error_response(
        429, "RATE_LIMITED", "Too many attempts. Please wait a minute and try again."
    )
    response.headers["Retry-After"] = "60"
    return response


def register_rate_limiting(app: FastAPI, settings: Settings) -> None:
    _limits["auth"] = settings.AUTH_RATE_LIMIT
    _limits["lookup"] = settings.LOOKUP_RATE_LIMIT
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _handle_rate_limited)
