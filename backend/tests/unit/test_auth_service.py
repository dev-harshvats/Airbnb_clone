"""AuthService against in-memory ports: no database, no HTTP (Dependency Inversion)."""

from datetime import date, timedelta

import pytest

from app.adapters.security.bcrypt_hasher import BcryptHasher
from app.adapters.security.jwt_codec import JwtCodec
from app.domain.entities import ClientInfo
from app.domain.errors import DomainError, ErrorKind
from app.domain.tokens import hash_token
from app.services.auth_service import AuthService
from tests.conftest import TEST_NOW
from tests.fakes.clock import FixedClock
from tests.fakes.uow import InMemoryUnitOfWork

CLIENT = ClientInfo(ip="203.0.113.7", user_agent="pytest")
SIGNUP = {
    "email": "harsh@example.com",
    "password": "Password123",
    "first_name": "Harsh",
    "last_name": "Vats",
    "date_of_birth": date(1995, 5, 17),
    "client": CLIENT,
}


@pytest.fixture
def clock():
    return FixedClock(TEST_NOW)


@pytest.fixture
def uow():
    return InMemoryUnitOfWork()


@pytest.fixture
def service(uow, clock):
    codec = JwtCodec(
        "unit-test-secret-unit-test-secret-0123456789",
        access_ttl=timedelta(minutes=15),
        refresh_ttl=timedelta(days=7),
        clock=clock,
    )
    return AuthService(uow=uow, hasher=BcryptHasher(4), tokens=codec, clock=clock)


def error_of(call) -> DomainError:
    with pytest.raises(DomainError) as info:
        call()
    return info.value


def test_signup_stores_only_a_hash_of_the_refresh_token(service, uow):
    session = service.signup(**SIGNUP)
    stored = uow.refresh_tokens.get_by_hash(hash_token(session.refresh_token))
    assert stored is not None and stored.token_hash != session.refresh_token
    assert stored.user_id == session.user.id
    assert (stored.ip, stored.user_agent) == ("203.0.113.7", "pytest")
    assert stored.expires_at == session.refresh_expires_at
    assert uow.users.get_by_email("harsh@example.com").password_hash != "Password123"


def test_signup_persists_atomically(service, uow):
    service.signup(**SIGNUP)
    uow.discard_uncommitted()  # simulate the request ending without a commit
    assert uow.users.get_by_email("harsh@example.com") is not None
    assert len(uow.refresh_tokens.rows) == 1


def test_duplicate_signup_is_a_conflict(service):
    service.signup(**SIGNUP)
    err = error_of(lambda: service.signup(**SIGNUP))
    assert (err.kind, err.code) == (ErrorKind.CONFLICT, "EMAIL_TAKEN")


def test_login_failure_modes_share_one_error(service):
    service.signup(**SIGNUP)
    wrong = error_of(
        lambda: service.login(email="harsh@example.com", password="Nope12345", client=CLIENT)
    )
    unknown = error_of(
        lambda: service.login(email="ghost@example.com", password="Nope12345", client=CLIENT)
    )
    assert (wrong.kind, wrong.code, wrong.detail) == (unknown.kind, unknown.code, unknown.detail)
    assert wrong.code == "INVALID_CREDENTIALS"


def test_each_login_starts_a_new_family(service, uow):
    service.signup(**SIGNUP)
    service.login(email="harsh@example.com", password="Password123", client=CLIENT)
    families = {t.family_id for t in uow.refresh_tokens.rows.values()}
    assert len(families) == 2


def test_refresh_links_old_token_to_its_replacement(service, uow):
    first = service.signup(**SIGNUP)
    second = service.refresh(first.refresh_token, CLIENT)

    old = uow.refresh_tokens.get_by_hash(hash_token(first.refresh_token))
    new = uow.refresh_tokens.get_by_hash(hash_token(second.refresh_token))
    assert old.revoked_at == TEST_NOW
    assert old.replaced_by_id == new.id
    assert new.family_id == old.family_id and new.revoked_at is None


def test_reuse_revokes_family_and_that_revocation_is_committed(service, uow):
    first = service.signup(**SIGNUP)
    second = service.refresh(first.refresh_token, CLIENT)

    err = error_of(lambda: service.refresh(first.refresh_token, CLIENT))
    assert (err.kind, err.code) == (ErrorKind.UNAUTHENTICATED, "INVALID_TOKEN")

    uow.discard_uncommitted()  # the error must not roll the revocation back
    newest = uow.refresh_tokens.get_by_hash(hash_token(second.refresh_token))
    assert newest.revoked_at is not None


def test_refresh_fails_when_the_user_no_longer_exists(service, uow):
    session = service.signup(**SIGNUP)
    uow.users.rows.clear()
    assert error_of(lambda: service.refresh(session.refresh_token, CLIENT)).code == "INVALID_TOKEN"


def test_logout_revokes_the_whole_family_and_ignores_unknown_tokens(service, uow):
    first = service.signup(**SIGNUP)
    second = service.refresh(first.refresh_token, CLIENT)
    service.logout(second.refresh_token)
    service.logout("not-a-real-token")
    service.logout(None)

    assert all(t.revoked_at is not None for t in uow.refresh_tokens.rows.values())
