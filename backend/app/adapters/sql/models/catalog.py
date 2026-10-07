"""Experiences and services: hosted activities and local professionals shown on those tabs.

They are browse-only in this version (no reservations), so ratings are stored on the row rather
than computed from reviews, like the rest of the mocked catalogue data."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.sql.models.mixins import now_column, string_enum
from app.core.database import Base
from app.domain.enums import ExperienceCategory, ListingStatus, ServiceType


class ExperienceModel(Base):
    __tablename__ = "experiences"
    __table_args__ = (
        CheckConstraint("price_per_guest > 0", name="price_positive"),
        CheckConstraint("duration_minutes > 0", name="duration_positive"),
        CheckConstraint("max_guests > 0", name="max_guests_positive"),
        CheckConstraint("rating_avg IS NULL OR rating_avg BETWEEN 1 AND 5", name="rating_range"),
        Index("ix_experiences_status_city", "status", "city"),
        Index("ix_experiences_category", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[ExperienceCategory] = mapped_column(
        string_enum(ExperienceCategory, "experience_category")
    )
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    latitude: Mapped[float]
    longitude: Mapped[float]
    start_time: Mapped[str] = mapped_column(String(5))  # HH:MM, local time
    duration_minutes: Mapped[int]
    price_per_guest: Mapped[int]  # whole rupees
    max_guests: Mapped[int]
    rating_avg: Mapped[float | None]
    review_count: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    status: Mapped[ListingStatus] = mapped_column(
        string_enum(ListingStatus, "experience_status"),
        default=ListingStatus.ACTIVE,
        server_default=ListingStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = now_column()


class ExperiencePhotoModel(Base):
    __tablename__ = "experience_photos"
    __table_args__ = (
        UniqueConstraint(
            "experience_id", "position", name="uq_experience_photos_experience_id_position"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    experience_id: Mapped[int] = mapped_column(ForeignKey("experiences.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(500))
    card_url: Mapped[str] = mapped_column(String(500))
    position: Mapped[int]


class ServiceModel(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("price_from > 0", name="price_positive"),
        CheckConstraint("rating_avg IS NULL OR rating_avg BETWEEN 1 AND 5", name="rating_range"),
        Index("ix_services_status_city", "status", "city"),
        Index("ix_services_type", "service_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    service_type: Mapped[ServiceType] = mapped_column(string_enum(ServiceType, "service_type"))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    price_from: Mapped[int]  # whole rupees
    price_unit: Mapped[str] = mapped_column(String(20))  # "guest", "hour" or "session"
    is_popular: Mapped[bool] = mapped_column(default=False, server_default=text("0"))
    rating_avg: Mapped[float | None]
    review_count: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    status: Mapped[ListingStatus] = mapped_column(
        string_enum(ListingStatus, "service_status"),
        default=ListingStatus.ACTIVE,
        server_default=ListingStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = now_column()


class ServicePhotoModel(Base):
    __tablename__ = "service_photos"
    __table_args__ = (
        UniqueConstraint("service_id", "position", name="uq_service_photos_service_id_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(500))
    card_url: Mapped[str] = mapped_column(String(500))
    position: Mapped[int]
