import itertools
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.security.bcrypt_hasher import BcryptHasher
from app.adapters.security.jwt_codec import JwtCodec
from app.adapters.sql.uow import SqlUnitOfWork
from app.core.config import Settings
from app.core.container import get_clock
from app.core.database import Base
from app.core.rate_limit import limiter
from app.domain.entities import NewUser, User
from app.main import create_app
from tests.factories import Factory
from tests.fakes.clock import FixedClock

TEST_NOW = datetime(2026, 10, 7, 6, 30, tzinfo=UTC)  # 12:00 in India


@pytest.fixture
def settings(tmp_path) -> Settings:
    # _env_file=None: tests must not depend on a developer's local backend/.env
    return Settings(
        _env_file=None,
        ENV="test",
        DATABASE_URL=f"sqlite:///{tmp_path / 'test.db'}",
        MEDIA_DIR=tmp_path / "media",
        JWT_SECRET="test-secret-test-secret-test-secret-0123456789",
        BCRYPT_ROUNDS=4,
        CORS_ORIGINS=["http://localhost:3000"],
    )


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(TEST_NOW)


@pytest.fixture(autouse=True)
def _fresh_rate_limits() -> Iterator[None]:
    limiter.reset()
    yield
    limiter.reset()


def build_app(settings: Settings, clock: FixedClock) -> FastAPI:
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    app.dependency_overrides[get_clock] = lambda: clock
    return app


@pytest.fixture
def app(settings, clock) -> FastAPI:
    return build_app(settings, clock)


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_client(settings, clock) -> Iterator[Callable[..., TestClient]]:
    """Build a client whose settings differ from the defaults."""
    opened: list[TestClient] = []

    def _make(**overrides) -> TestClient:
        c = TestClient(build_app(settings.model_copy(update=overrides), clock))
        c.__enter__()
        opened.append(c)
        return c

    yield _make
    for c in opened:
        c.__exit__(None, None, None)


@pytest.fixture
def make_user(app, settings, clock) -> Callable[..., tuple[User, str]]:
    """Insert a user straight through the repository and return (user, access_token)."""
    counter = itertools.count(1)

    def _make(password: str = "Password123", **overrides) -> tuple[User, str]:
        n = next(counter)
        fields = {
            "email": f"user{n}@example.com",
            "first_name": "Test",
            "last_name": f"User{n}",
            "date_of_birth": date(1995, 5, 17),
            "avatar_url": None,
            "bio": None,
            "is_host": False,
            "is_superhost": False,
            "created_at": clock.now(),
            "updated_at": clock.now(),
        } | overrides
        fields["password_hash"] = BcryptHasher(settings.BCRYPT_ROUNDS).hash(password)
        with app.state.session_factory() as session:
            uow = SqlUnitOfWork(session)
            user = uow.users.add(NewUser(**fields))
            uow.commit()
        codec = JwtCodec(
            settings.JWT_SECRET,
            access_ttl=settings.access_ttl,
            refresh_ttl=settings.refresh_ttl,
            clock=clock,
        )
        return user, codec.create_access_token(user.id).token

    return _make


@pytest.fixture
def factory(app, clock) -> Factory:
    return Factory(app, clock)


@pytest.fixture
def auth():
    """`auth(token)` -> the Authorization header for a request."""
    return lambda token: {"Authorization": f"Bearer {token}"}
