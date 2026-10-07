from datetime import date, datetime

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.sql.models.mixins import now_column
from app.adapters.sql.types import UTCDateTime
from app.core.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)  # stored lower-cased
    password_hash: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    date_of_birth: Mapped[date]
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(String(500))
    is_host: Mapped[bool] = mapped_column(default=False, server_default=text("0"))
    is_superhost: Mapped[bool] = mapped_column(default=False, server_default=text("0"))
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class RefreshTokenModel(Base):
    """One row per issued refresh token. Tokens of one login share a `family_id`, which lets
    the server revoke the whole chain when an already-rotated token is replayed."""

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_family_id", "family_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)  # sha256 hex digest
    family_id: Mapped[str] = mapped_column(String(32))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    replaced_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL")
    )
    user_agent: Mapped[str | None] = mapped_column(String(300))
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = now_column()
