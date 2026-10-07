"""Every implementation of the persistence ports must satisfy the same contract (Liskov)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.adapters.sql.uow import SqlUnitOfWork
from app.core.database import Base, build_engine, build_session_factory
from app.domain.entities import NewRefreshToken, NewUser
from app.domain.errors import DomainError, ErrorKind

NOW = datetime(2026, 10, 7, 6, 30, tzinfo=UTC)


@pytest.fixture(params=["memory", "sql"])
def uow(request, tmp_path):
    if request.param == "memory":
        from tests.fakes.uow import InMemoryUnitOfWork

        yield InMemoryUnitOfWork()
        return
    engine = build_engine(f"sqlite:///{tmp_path / 'contract.db'}")
    Base.metadata.create_all(engine)
    with build_session_factory(engine)() as session:
        yield SqlUnitOfWork(session)
    engine.dispose()


def new_user(email="a@example.com", **kw) -> NewUser:
    return NewUser(
        **{
            "email": email,
            "password_hash": "hash",
            "first_name": "Asha",
            "last_name": "Rao",
            "date_of_birth": date(1990, 4, 1),
            "avatar_url": None,
            "bio": None,
            "is_host": False,
            "is_superhost": False,
            "created_at": NOW,
            "updated_at": NOW,
        }
        | kw
    )


def new_token(user_id, token_hash="h1", family_id="fam-1", **kw) -> NewRefreshToken:
    return NewRefreshToken(
        **{
            "user_id": user_id,
            "token_hash": token_hash,
            "family_id": family_id,
            "expires_at": NOW + timedelta(days=7),
            "user_agent": "pytest",
            "ip": "127.0.0.1",
            "created_at": NOW,
        }
        | kw
    )


# ---------- UserRepository ----------


def test_add_then_read_back_by_id_and_email(uow):
    created = uow.users.add(new_user())
    uow.commit()
    assert created.id is not None
    assert uow.users.get_by_id(created.id) == created
    assert uow.users.get_by_email("a@example.com") == created
    assert created.created_at == NOW and created.created_at.tzinfo is not None


def test_missing_user_is_none(uow):
    assert uow.users.get_by_id(404) is None
    assert uow.users.get_by_email("nobody@example.com") is None


def test_duplicate_email_raises_conflict_and_leaves_the_unit_usable(uow):
    uow.users.add(new_user())
    uow.commit()
    with pytest.raises(DomainError) as info:
        uow.users.add(new_user())
    assert (info.value.kind, info.value.code) == (ErrorKind.CONFLICT, "EMAIL_TAKEN")
    assert uow.users.add(new_user("b@example.com")).id is not None


def test_update_persists_changes(uow):
    from dataclasses import replace

    created = uow.users.add(new_user())
    uow.users.update(replace(created, is_host=True, bio="Hello"))
    uow.commit()
    again = uow.users.get_by_id(created.id)
    assert again.is_host is True and again.bio == "Hello"


# ---------- RefreshTokenStore ----------


def test_token_round_trip_by_hash(uow):
    user = uow.users.add(new_user())
    token = uow.refresh_tokens.add(new_token(user.id))
    uow.commit()
    found = uow.refresh_tokens.get_by_hash("h1")
    assert found == token
    assert found.revoked_at is None and found.replaced_by_id is None
    assert uow.refresh_tokens.get_by_hash("unknown") is None


def test_revoke_records_time_and_replacement(uow):
    user = uow.users.add(new_user())
    old = uow.refresh_tokens.add(new_token(user.id, "h1"))
    new = uow.refresh_tokens.add(new_token(user.id, "h2"))
    uow.refresh_tokens.revoke(old.id, NOW, replaced_by_id=new.id)
    uow.commit()
    found = uow.refresh_tokens.get_by_hash("h1")
    assert found.revoked_at == NOW and found.replaced_by_id == new.id


def test_revoke_family_only_touches_that_families_live_tokens(uow):
    user = uow.users.add(new_user())
    a1 = uow.refresh_tokens.add(new_token(user.id, "a1", family_id="A"))
    uow.refresh_tokens.add(new_token(user.id, "a2", family_id="A"))
    uow.refresh_tokens.add(new_token(user.id, "b1", family_id="B"))
    earlier = NOW - timedelta(hours=1)
    uow.refresh_tokens.revoke(a1.id, earlier)

    assert uow.refresh_tokens.revoke_family("A", NOW) == 1  # a1 was already revoked
    assert uow.refresh_tokens.get_by_hash("a1").revoked_at == earlier  # not overwritten
    assert uow.refresh_tokens.get_by_hash("a2").revoked_at == NOW
    assert uow.refresh_tokens.get_by_hash("b1").revoked_at is None
    assert uow.refresh_tokens.revoke_family("nope", NOW) == 0


def test_purge_expired_removes_only_tokens_that_can_no_longer_be_used(uow):
    user = uow.users.add(new_user())
    uow.refresh_tokens.add(new_token(user.id, "old", expires_at=NOW - timedelta(days=1)))
    uow.refresh_tokens.add(new_token(user.id, "live", expires_at=NOW + timedelta(days=1)))
    uow.commit()

    assert uow.refresh_tokens.purge_expired(NOW) == 1
    assert uow.refresh_tokens.get_by_hash("old") is None
    assert uow.refresh_tokens.get_by_hash("live") is not None
