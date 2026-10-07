from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.sql.models.mixins import now_column
from app.core.database import Base

_RATING_COLUMNS = (
    "rating",
    "cleanliness",
    "accuracy",
    "check_in",
    "communication",
    "location",
    "value",
)


class ReviewModel(Base):
    """A guest's review of one completed stay (at most one per booking)."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint(
            " AND ".join(f"{c} BETWEEN 1 AND 5" for c in _RATING_COLUMNS), name="ratings_in_range"
        ),
        Index("ix_reviews_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="RESTRICT"), unique=True
    )
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="RESTRICT"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    rating: Mapped[int]  # overall
    cleanliness: Mapped[int]
    accuracy: Mapped[int]
    check_in: Mapped[int]
    communication: Mapped[int]
    location: Mapped[int]
    value: Mapped[int]
    comment: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = now_column()
