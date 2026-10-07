"""Composition root: the one place where concrete adapters are chosen and wired to ports.

Routers and services depend only on the abstractions; tests replace any provider with
`app.dependency_overrides[provider] = ...` (for example `get_clock` with a fixed clock).
"""

from typing import Annotated

from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.adapters.clock import SystemClock
from app.adapters.security.bcrypt_hasher import BcryptHasher
from app.adapters.security.jwt_codec import JwtCodec
from app.adapters.sql.uow import SqlUnitOfWork
from app.adapters.storage.local_storage import LocalStorage
from app.adapters.storage.pillow_processor import PillowImageProcessor
from app.core.config import Settings
from app.core.database import DbSession
from app.domain.entities import User
from app.domain.errors import DomainError, ErrorKind
from app.domain.pricing import FeeRule, default_rules
from app.ports.clock import Clock
from app.ports.security import PasswordHasher, TokenCodec
from app.ports.storage import ImageProcessor, StorageBackend
from app.ports.uow import UnitOfWork
from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.catalog_service import CatalogService
from app.services.host_service import HostService
from app.services.listing_service import ListingService
from app.services.media_service import MediaService
from app.services.review_service import ReviewService
from app.services.search_service import SearchService
from app.services.user_service import UserService
from app.services.wishlist_service import WishlistService

_bearer = HTTPBearer(auto_error=False, description="Short-lived access token from /auth/login")


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_clock() -> Clock:
    return SystemClock()


ClockDep = Annotated[Clock, Depends(get_clock)]


def get_hasher(settings: SettingsDep) -> PasswordHasher:
    return BcryptHasher(settings.BCRYPT_ROUNDS)


HasherDep = Annotated[PasswordHasher, Depends(get_hasher)]


def get_token_codec(settings: SettingsDep, clock: ClockDep) -> TokenCodec:
    return JwtCodec(settings.JWT_SECRET, settings.access_ttl, settings.refresh_ttl, clock)


TokenCodecDep = Annotated[TokenCodec, Depends(get_token_codec)]


def get_uow(db: DbSession) -> UnitOfWork:
    return SqlUnitOfWork(db)


UowDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_auth_service(
    uow: UowDep, hasher: HasherDep, tokens: TokenCodecDep, clock: ClockDep
) -> AuthService:
    return AuthService(uow, hasher, tokens, clock)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(uow: UowDep, clock: ClockDep) -> UserService:
    return UserService(uow, clock)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_fee_rules(settings: SettingsDep) -> tuple[FeeRule, ...]:
    return default_rules(settings.SERVICE_FEE_RATE, settings.TAX_RATE)


FeeRulesDep = Annotated[tuple[FeeRule, ...], Depends(get_fee_rules)]


def get_storage(settings: SettingsDep) -> StorageBackend:
    return LocalStorage(settings.MEDIA_DIR)


def get_image_processor() -> ImageProcessor:
    return PillowImageProcessor()


def get_media_service(
    storage: Annotated[StorageBackend, Depends(get_storage)],
    images: Annotated[ImageProcessor, Depends(get_image_processor)],
) -> MediaService:
    return MediaService(storage, images)


def get_search_service(uow: UowDep, rules: FeeRulesDep) -> SearchService:
    return SearchService(uow, rules)


def get_listing_service(uow: UowDep, clock: ClockDep, rules: FeeRulesDep) -> ListingService:
    return ListingService(uow, clock, rules)


def get_booking_service(uow: UowDep, clock: ClockDep, rules: FeeRulesDep) -> BookingService:
    return BookingService(uow, clock, rules)


def get_review_service(uow: UowDep, clock: ClockDep) -> ReviewService:
    return ReviewService(uow, clock)


def get_wishlist_service(uow: UowDep, clock: ClockDep) -> WishlistService:
    return WishlistService(uow, clock)


def get_host_service(
    uow: UowDep, clock: ClockDep, media: Annotated[MediaService, Depends(get_media_service)]
) -> HostService:
    return HostService(uow, clock, media)


def get_catalog_service(uow: UowDep) -> CatalogService:
    return CatalogService(uow)


SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
ListingServiceDep = Annotated[ListingService, Depends(get_listing_service)]
BookingServiceDep = Annotated[BookingService, Depends(get_booking_service)]
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
WishlistServiceDep = Annotated[WishlistService, Depends(get_wishlist_service)]
HostServiceDep = Annotated[HostService, Depends(get_host_service)]


def no_store(response: Response) -> None:
    """Responses about the logged-in user must never be cached by browsers or proxies."""
    response.headers["Cache-Control"] = "no-store"


NoStore = Depends(no_store)


# ---------- who is calling ----------

BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _user_for_token(token: str, tokens: TokenCodec, uow: UnitOfWork) -> User:
    claims = tokens.decode_token(token, "access")
    user = uow.users.get_by_id(claims.user_id)
    if user is None:  # the account was deleted after the token was issued
        raise DomainError(
            ErrorKind.UNAUTHENTICATED, "INVALID_TOKEN", "Your session is invalid or has expired."
        )
    return user


def get_current_user(credentials: BearerDep, tokens: TokenCodecDep, uow: UowDep) -> User:
    if credentials is None:
        raise DomainError(ErrorKind.UNAUTHENTICATED, "NOT_AUTHENTICATED", "Log in to continue.")
    return _user_for_token(credentials.credentials, tokens, uow)


def get_optional_user(credentials: BearerDep, tokens: TokenCodecDep, uow: UowDep) -> User | None:
    """No credentials means anonymous. A token that is present but bad is still a 401, so the
    client knows to refresh it instead of silently being treated as logged out."""
    if credentials is None:
        return None
    return _user_for_token(credentials.credentials, tokens, uow)


def require_host(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_host:
        raise DomainError(ErrorKind.FORBIDDEN, "NOT_HOST", "Switch to hosting to do this.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
HostUser = Annotated[User, Depends(require_host)]
