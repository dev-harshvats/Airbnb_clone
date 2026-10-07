from fastapi import APIRouter

from app.core.database import DbSession, database_is_up
from app.core.errors import AppError

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok"}


@router.get("/ready")
def ready(db: DbSession) -> dict[str, str]:
    """Readiness: the database answers."""
    if not database_is_up(db):
        raise AppError(503, "NOT_READY", "Database unavailable")
    return {"status": "ready", "database": "ok"}
