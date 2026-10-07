from typing import Annotated

from fastapi import APIRouter, Cookie, Request, Response

from app.api.cookies import REFRESH_COOKIE, clear_refresh_cookie, set_refresh_cookie
from app.api.guards import ClientInfoDep, TrustedOrigin
from app.core.container import AuthServiceDep, CurrentUser, NoStore, SettingsDep
from app.core.rate_limit import auth_limit, limiter, lookup_limit
from app.domain.entities import AuthSession
from app.domain.errors import DomainError, ErrorKind
from app.schemas.auth import (
    AuthResponse,
    CheckEmailRequest,
    CheckEmailResponse,
    LoginRequest,
    SignupRequest,
)
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[NoStore])


def _auth_response(session: AuthSession, response: Response, settings) -> AuthResponse:
    set_refresh_cookie(response, session, settings)
    return AuthResponse(
        access_token=session.access_token,
        expires_in=int(settings.access_ttl.total_seconds()),
        user=UserOut.model_validate(session.user),
    )


@router.post("/check-email", response_model=CheckEmailResponse)
@limiter.limit(lookup_limit)
def check_email(request: Request, body: CheckEmailRequest, service: AuthServiceDep):
    return CheckEmailResponse(exists=service.check_email(body.email))


@router.post("/signup", response_model=AuthResponse, status_code=201)
@limiter.limit(auth_limit)
def signup(
    request: Request,
    response: Response,
    body: SignupRequest,
    service: AuthServiceDep,
    client: ClientInfoDep,
    settings: SettingsDep,
):
    session = service.signup(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        date_of_birth=body.date_of_birth,
        client=client,
    )
    return _auth_response(session, response, settings)


@router.post("/login", response_model=AuthResponse)
@limiter.limit(auth_limit)
def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    service: AuthServiceDep,
    client: ClientInfoDep,
    settings: SettingsDep,
):
    session = service.login(email=body.email, password=body.password, client=client)
    return _auth_response(session, response, settings)


@router.post("/refresh", response_model=AuthResponse, dependencies=[TrustedOrigin])
def refresh(
    response: Response,
    service: AuthServiceDep,
    client: ClientInfoDep,
    settings: SettingsDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    if not refresh_token:
        raise DomainError(ErrorKind.UNAUTHENTICATED, "MISSING_REFRESH_TOKEN", "Log in to continue.")
    session = service.refresh(refresh_token, client)
    return _auth_response(session, response, settings)


@router.post("/logout", status_code=204, dependencies=[TrustedOrigin])
def logout(
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    service.logout(refresh_token)
    clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
