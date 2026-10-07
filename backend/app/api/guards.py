"""Request-level protections and helpers shared by routers."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.errors import AppError
from app.core.http import client_ip
from app.domain.entities import ClientInfo


def enforce_trusted_origin(request: Request) -> None:
    """Reject cookie-authenticated requests that a browser sent from another website (CSRF).

    Browsers always attach `Origin` to cross-site POSTs, so a foreign origin is refused. A missing
    `Origin` comes from non-browser callers such as server-side code, which cannot be tricked into
    riding a visitor's cookies, so it is allowed.
    """
    origin = request.headers.get("origin")
    if origin is not None and origin not in request.app.state.settings.CORS_ORIGINS:
        raise AppError(403, "BAD_ORIGIN", "This request was blocked because of where it came from.")


TrustedOrigin = Depends(enforce_trusted_origin)


def get_client_info(request: Request) -> ClientInfo:
    user_agent = request.headers.get("user-agent")
    return ClientInfo(ip=client_ip(request), user_agent=user_agent[:300] if user_agent else None)


ClientInfoDep = Annotated[ClientInfo, Depends(get_client_info)]
