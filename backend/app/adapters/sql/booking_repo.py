from dataclasses import asdict
from datetime import date, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.adapters.sql.models import BookingModel
from app.domain.entities import Booking, NewBooking
from app.domain.enums import BookingStatus


def to_booking(row: BookingModel) -> Booking:
    return Booking(
        id=row.id,
        code=row.code,
        listing_id=row.listing_id,
        guest_id=row.guest_id,
        check_in=row.check_in,
        check_out=row.check_out,
        adults=row.adults,
        children=row.children,
        infants=row.infants,
        pets=row.pets,
        nightly_rate=row.nightly_rate,
        nights=row.nights,
        subtotal=row.subtotal,
        cleaning_fee=row.cleaning_fee,
        service_fee=row.service_fee,
        taxes=row.taxes,
        total=row.total,
        payment_method=row.payment_method_mock,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
        status=row.status,
        cancelled_at=row.cancelled_at,
    )


def _overlapping(listing_id: int, check_in: date, check_out: date):
    """Confirmed stays that overlap [check_in, check_out): they start before it ends and end
    after it starts. Equal boundaries (back-to-back stays) do not count."""
    return (
        BookingModel.listing_id == listing_id,
        BookingModel.status == BookingStatus.CONFIRMED,
        BookingModel.check_in < check_out,
        BookingModel.check_out > check_in,
    )


class SqlBookingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, new: NewBooking) -> Booking:
        data = asdict(new)
        data["payment_method_mock"] = data.pop("payment_method")
        row = BookingModel(**data)
        self._session.add(row)
        self._session.flush()
        return to_booking(row)

    def get_by_code(self, code: str) -> Booking | None:
        row = self._session.scalar(select(BookingModel).where(BookingModel.code == code))
        return to_booking(row) if row else None

    def get_by_idempotency_key(self, guest_id: int, key: str) -> Booking | None:
        row = self._session.scalar(
            select(BookingModel).where(
                BookingModel.guest_id == guest_id, BookingModel.idempotency_key == key
            )
        )
        return to_booking(row) if row else None

    def has_overlap(self, listing_id: int, check_in: date, check_out: date) -> bool:
        return (
            self._session.scalar(
                select(BookingModel.id)
                .where(*_overlapping(listing_id, check_in, check_out))
                .limit(1)
            )
            is not None
        )

    def booked_ranges(self, listing_id: int, start: date, end: date) -> list[tuple[date, date]]:
        rows = self._session.execute(
            select(BookingModel.check_in, BookingModel.check_out)
            .where(*_overlapping(listing_id, start, end))
            .order_by(BookingModel.check_in)
        ).all()
        return [(r[0], r[1]) for r in rows]

    def mark_cancelled(self, booking_id: int, when: datetime) -> Booking:
        self._session.execute(
            update(BookingModel)
            .where(BookingModel.id == booking_id)
            .values(status=BookingStatus.CANCELLED, cancelled_at=when)
        )
        row = self._session.get(BookingModel, booking_id)
        self._session.refresh(row)
        return to_booking(row)

    def list_for_guest(self, guest_id: int) -> list[Booking]:
        rows = self._session.scalars(
            select(BookingModel)
            .where(BookingModel.guest_id == guest_id)
            .order_by(BookingModel.check_in.desc(), BookingModel.id.desc())
        )
        return [to_booking(r) for r in rows]
