import logging
import uuid

from app.core.logging import log_event
from app.domain.auth_policy import is_adult, normalize_email
from app.domain.entities import (
    AuthSession,
    ClientInfo,
    NewRefreshToken,
    NewUser,
    RefreshToken,
    User,
)
from app.domain.errors import DomainError, ErrorKind
from app.domain.tokens import hash_token
from app.ports.clock import Clock
from app.ports.security import PasswordHasher, TokenCodec
from app.ports.uow import UnitOfWork

logger = logging.getLogger("app.auth")


def _invalid_token() -> DomainError:
    return DomainError(
        ErrorKind.UNAUTHENTICATED, "INVALID_TOKEN", "Your session is invalid or has expired."
    )


class AuthService:
    def __init__(
        self, uow: UnitOfWork, hasher: PasswordHasher, tokens: TokenCodec, clock: Clock
    ) -> None:
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock

    def check_email(self, email: str) -> bool:
        return self._uow.users.get_by_email(normalize_email(email)) is not None

    def signup(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        date_of_birth,
        client: ClientInfo,
    ) -> AuthSession:
        if not is_adult(date_of_birth, self._clock.today()):
            raise DomainError(
                ErrorKind.UNPROCESSABLE,
                "UNDER_AGE",
                "You must be at least 18 years old to sign up.",
            )
        now = self._clock.now()
        user = self._uow.users.add(
            NewUser(
                email=normalize_email(email),
                password_hash=self._hasher.hash(password),
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                avatar_url=None,
                bio=None,
                is_host=False,
                is_superhost=False,
                created_at=now,
                updated_at=now,
            )
        )
        session, _ = self._issue(user, client, family_id=uuid.uuid4().hex)
        self._uow.commit()
        log_event(logger, logging.INFO, "auth.signup", user_id=user.id)
        return session

    def login(self, *, email: str, password: str, client: ClientInfo) -> AuthSession:
        user = self._uow.users.get_by_email(normalize_email(email))
        # Verify even when there is no such user, so response time does not reveal accounts.
        password_ok = self._hasher.verify(password, user.password_hash if user else None)
        if user is None or not password_ok:
            raise DomainError(
                ErrorKind.UNAUTHENTICATED, "INVALID_CREDENTIALS", "Incorrect email or password."
            )
        session, _ = self._issue(user, client, family_id=uuid.uuid4().hex)
        self._uow.commit()
        log_event(logger, logging.INFO, "auth.login", user_id=user.id)
        return session

    def refresh(self, raw_token: str, client: ClientInfo) -> AuthSession:
        """Rotate a refresh token. Presenting one that was already rotated means it leaked, so
        the whole family is revoked (the legitimate holder simply has to log in again)."""
        self._tokens.decode_token(raw_token, "refresh")  # signature, type and expiry
        record = self._uow.refresh_tokens.get_by_hash(hash_token(raw_token))
        if record is None:
            raise _invalid_token()

        now = self._clock.now()
        if record.revoked_at is not None:
            self._uow.refresh_tokens.revoke_family(record.family_id, now)
            self._uow.commit()  # persist the revocation even though we are about to raise
            log_event(
                logger,
                logging.WARNING,
                "auth.refresh_reuse_detected",
                user_id=record.user_id,
                family_id=record.family_id,
            )
            raise _invalid_token()
        if record.expires_at <= now:
            raise _invalid_token()

        user = self._uow.users.get_by_id(record.user_id)
        if user is None:
            raise _invalid_token()
        session, new_record = self._issue(user, client, family_id=record.family_id)
        self._uow.refresh_tokens.revoke(record.id, now, replaced_by_id=new_record.id)
        self._uow.commit()
        return session

    def logout(self, raw_token: str | None) -> None:
        """End the session this refresh token belongs to. Always succeeds (idempotent)."""
        if not raw_token:
            return
        record = self._uow.refresh_tokens.get_by_hash(hash_token(raw_token))
        if record is not None:
            self._uow.refresh_tokens.revoke_family(record.family_id, self._clock.now())
            self._uow.commit()

    def _issue(
        self, user: User, client: ClientInfo, family_id: str
    ) -> tuple[AuthSession, RefreshToken]:
        access = self._tokens.create_access_token(user.id)
        refresh = self._tokens.create_refresh_token(user.id, family_id)
        record = self._uow.refresh_tokens.add(
            NewRefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh.token),
                family_id=family_id,
                expires_at=refresh.expires_at,
                user_agent=client.user_agent,
                ip=client.ip,
                created_at=self._clock.now(),
            )
        )
        session = AuthSession(
            user, access.token, access.expires_at, refresh.token, refresh.expires_at
        )
        return session, record
