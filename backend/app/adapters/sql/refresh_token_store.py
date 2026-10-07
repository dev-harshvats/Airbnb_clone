from dataclasses import asdict
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.adapters.sql.models import RefreshTokenModel
from app.domain.entities import NewRefreshToken, RefreshToken


def to_refresh_token(row: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        family_id=row.family_id,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        replaced_by_id=row.replaced_by_id,
        user_agent=row.user_agent,
        ip=row.ip,
        created_at=row.created_at,
    )


class SqlRefreshTokenStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, new: NewRefreshToken) -> RefreshToken:
        row = RefreshTokenModel(**asdict(new))
        self._session.add(row)
        self._session.flush()
        return to_refresh_token(row)

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        row = self._session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        return to_refresh_token(row) if row else None

    def revoke(self, token_id: int, when: datetime, replaced_by_id: int | None = None) -> None:
        self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id)
            .values(revoked_at=when, replaced_by_id=replaced_by_id)
        )

    def revoke_family(self, family_id: str, when: datetime) -> int:
        result = self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == family_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=when)
        )
        return result.rowcount

    def purge_expired(self, before: datetime) -> int:
        result = self._session.execute(
            delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < before)
        )
        return result.rowcount
