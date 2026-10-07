from collections.abc import Sequence
from dataclasses import asdict
from datetime import date

from app.domain.booking_policy import is_completed, is_upcoming, validate_booking
from app.domain.codes import generate_booking_code
from app.domain.entities import Booking, NewBooking, User
from app.domain.enums import BookingStatus, PaymentMethod
from app.domain.errors import DomainError, ErrorKind
from app.domain.pricing import FeeRule, calculate_quote
from app.ports.clock import Clock
from app.ports.uow import UnitOfWork
from app.schemas.booking import BookingCreate, BookingOut, TripScope
from app.services.listing_service import listing_not_found


def booking_not_found() -> DomainError:
    return DomainError(ErrorKind.NOT_FOUND, "BOOKING_NOT_FOUND", "Booking not found.")


class BookingService:
    def __init__(self, uow: UnitOfWork, clock: Clock, fee_rules: Sequence[FeeRule]) -> None:
        self._uow = uow
        self._clock = clock
        self._fee_rules = fee_rules

    def create(
        self, guest: User, data: BookingCreate, idempotency_key: str | None
    ) -> tuple[BookingOut, bool]:
        """Book a stay. Returns the booking and whether it was newly created: a retry that
        repeats an idempotency key gets the original booking back instead of a conflict."""
        today = self._clock.today()
        with self._uow.write():  # the free-dates check and the insert must not interleave
            if idempotency_key:
                existing = self._uow.bookings.get_by_idempotency_key(guest.id, idempotency_key)
                if existing is not None:
                    return self._view(existing, today), False

            listing = self._uow.listings.get(data.listing_id)
            if listing is None:
                raise listing_not_found()
            nights = validate_booking(
                listing,
                guest.id,
                data.check_in,
                data.check_out,
                data.adults,
                data.children,
                data.pets,
                today,
            )
            if self._uow.bookings.has_overlap(listing.id, data.check_in, data.check_out):
                raise DomainError(
                    ErrorKind.CONFLICT, "BOOKING_CONFLICT", "Those dates are no longer available."
                )
            quote = calculate_quote(
                listing.price_per_night, listing.cleaning_fee, nights, self._fee_rules
            )
            booking = self._uow.bookings.add(
                NewBooking(
                    code=generate_booking_code(),
                    listing_id=listing.id,
                    guest_id=guest.id,
                    check_in=data.check_in,
                    check_out=data.check_out,
                    adults=data.adults,
                    children=data.children,
                    infants=data.infants,
                    pets=data.pets,
                    nightly_rate=quote.nightly_rate,
                    nights=quote.nights,
                    subtotal=quote.subtotal,
                    cleaning_fee=quote.cleaning_fee,
                    service_fee=quote.service_fee,
                    taxes=quote.taxes,
                    total=quote.total,
                    payment_method=PaymentMethod(data.payment_method),
                    idempotency_key=idempotency_key,
                    created_at=self._clock.now(),
                )
            )
            self._uow.commit()
        return self._view(booking, today), True

    def trips(self, guest: User, scope: TripScope) -> list[BookingOut]:
        today = self._clock.today()
        bookings = self._uow.bookings.list_for_guest(guest.id)  # newest check-in first
        if scope == "upcoming":
            chosen = [b for b in bookings if is_upcoming(b, today)][::-1]  # soonest first
        elif scope == "past":
            chosen = [b for b in bookings if is_completed(b, today)]
        else:
            chosen = [b for b in bookings if b.status == BookingStatus.CANCELLED]
        return self._views(chosen, today)

    def get(self, guest: User, code: str) -> BookingOut:
        return self._view(self._own_booking(guest, code), self._clock.today())

    def cancel(self, guest: User, code: str) -> BookingOut:
        booking = self._own_booking(guest, code)
        today = self._clock.today()
        if booking.status == BookingStatus.CANCELLED:
            return self._view(booking, today)  # already cancelled: nothing to do
        if booking.check_in <= today:
            raise DomainError(
                ErrorKind.BAD_REQUEST,
                "CANNOT_CANCEL",
                "A stay that has started cannot be cancelled.",
            )
        cancelled = self._uow.bookings.mark_cancelled(booking.id, self._clock.now())
        self._uow.commit()
        return self._view(cancelled, today)

    # ---------- helpers ----------

    def _own_booking(self, guest: User, code: str) -> Booking:
        booking = self._uow.bookings.get_by_code(code)
        if booking is None or booking.guest_id != guest.id:  # never reveal others' bookings
            raise booking_not_found()
        return booking

    def _view(self, booking: Booking, today: date) -> BookingOut:
        return self._views([booking], today)[0]

    def _views(self, bookings: list[Booking], today: date) -> list[BookingOut]:
        summaries = self._uow.listing_reader.summaries([b.listing_id for b in bookings])
        reviewed = self._uow.reviews.reviewed_booking_ids([b.id for b in bookings])
        views = []
        for b in bookings:
            fields = asdict(b)
            for internal in ("id", "guest_id", "listing_id", "idempotency_key"):
                fields.pop(internal)
            views.append(
                BookingOut(
                    **fields,
                    listing=summaries[b.listing_id],
                    can_cancel=b.status == BookingStatus.CONFIRMED and b.check_in > today,
                    can_review=is_completed(b, today) and b.id not in reviewed,
                    has_review=b.id in reviewed,
                )
            )
        return views
