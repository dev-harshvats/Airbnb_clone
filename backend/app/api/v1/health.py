from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import DbSession
from app.core.errors import AppError

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok"}


@router.get("/ready")
def ready(db: DbSession) -> dict[str, str]:
    """Readiness: the database answers."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise AppError(503, "NOT_READY", "Database unavailable") from exc
    return {"status": "ready", "database": "ok"}
