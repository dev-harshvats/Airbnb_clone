"""SQLite engine and session factory.

Every connection enables WAL (concurrent readers during a write), foreign-key
enforcement and a busy timeout, so short write contention waits instead of failing.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import Engine, MetaData, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BUSY_TIMEOUT_MS = 5000

# Deterministic constraint names: migrations can then drop or alter them by name (SQLite needs
# this for batch operations) and diffs stay stable. Check constraints must be given a `name`.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def _ensure_sqlite_dir(url: str) -> None:
    prefix = "sqlite:///"
    if url.startswith(prefix) and ":memory:" not in url:
        Path(url[len(prefix) :]).parent.mkdir(parents=True, exist_ok=True)


def _apply_sqlite_pragmas(dbapi_conn, _record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    cursor.close()


def build_engine(url: str) -> Engine:
    _ensure_sqlite_dir(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _apply_sqlite_pragmas)
    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db(request: Request) -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db)]


def database_is_up(session: Session) -> bool:
    """Readiness probe: does the database answer a trivial query?"""
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
