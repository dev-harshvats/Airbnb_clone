"""SQLite engine and session factory.

Every connection enables WAL (concurrent readers during a write), foreign-key
enforcement and a busy timeout, so short write contention waits instead of failing.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BUSY_TIMEOUT_MS = 5000


class Base(DeclarativeBase):
    pass


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
