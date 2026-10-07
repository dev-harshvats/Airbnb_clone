from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.sql.models.mixins import now_column, string_enum
from app.adapters.sql.types import UTCDateTime
from app.core.database import Base
from app.domain.enums import BookingStatus, PaymentMethod


class BookingModel(Base):
    """A reservation. Stays are half-open intervals [check_in, check_out): the guest leaves on
    check_out, so another stay may start that same day. The price lines are a snapshot taken at
    booking time and never change when the host later edits the listing.

    Both foreign keys are RESTRICT: bookings are guests' trip history and financial records.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="dates_ordered"),
        CheckConstraint("nights > 0", name="nights_positive"),
        CheckConstraint("adults >= 1", name="adults_positive"),
        CheckConstraint("children >= 0 AND infants >= 0 AND pets >= 0", name="guests_non_negative"),
        CheckConstraint(
            "nightly_rate > 0 AND subtotal >= 0 AND cleaning_fee >= 0 AND service_fee >= 0 "
            "AND taxes >= 0 AND total >= 0",
            name="amounts_valid",
        ),
        UniqueConstraint(
            "guest_id", "idempotency_key", name="uq_bookings_guest_id_idempotency_key"
        ),
        Index("ix_bookings_availability", "listing_id", "status", "check_in", "check_out"),
        Index("ix_bookings_guest_id", "guest_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="RESTRICT"))
    guest_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    check_in: Mapped[date]
    check_out: Mapped[date]
    adults: Mapped[int]
    children: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    infants: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    pets: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    nightly_rate: Mapped[int]
    nights: Mapped[int]
    subtotal: Mapped[int]
    cleaning_fee: Mapped[int]
    service_fee: Mapped[int]
    taxes: Mapped[int]
    total: Mapped[int]
    status: Mapped[BookingStatus] = mapped_column(
        string_enum(BookingStatus, "booking_status"),
        default=BookingStatus.CONFIRMED,
        server_default=BookingStatus.CONFIRMED.value,
    )
    payment_method_mock: Mapped[PaymentMethod] = mapped_column(
        string_enum(PaymentMethod, "payment_method")
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(64))  # makes retries safe
    created_at: Mapped[datetime] = now_column()
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
