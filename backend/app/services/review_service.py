import logging
from dataclasses import replace

from app.core.logging import log_event
from app.domain.booking_policy import is_completed
from app.domain.entities import NewReview, User
from app.domain.errors import DomainError, ErrorKind
from app.domain.listing_rules import qualifies_as_superhost
from app.ports.clock import Clock
from app.ports.uow import UnitOfWork
from app.schemas.review import ReviewCreate
from app.services.booking_service import booking_not_found

logger = logging.getLogger("app.reviews")


class ReviewService:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def review_stay(self, guest: User, code: str, data: ReviewCreate) -> None:
        booking = self._uow.bookings.get_by_code(code)
        if booking is None or booking.guest_id != guest.id:
            raise booking_not_found()
        today = self._clock.today()
        if not is_completed(booking, today):
            raise DomainError(
                ErrorKind.BAD_REQUEST,
                "STAY_NOT_COMPLETED",
                "You can review a stay after you have checked out.",
            )
        categories = (
            data.cleanliness, data.accuracy, data.check_in,
            data.communication, data.location, data.value,
        )  # fmt: skip
        overall = data.rating or (2 * sum(categories) + 6) // 12  # average, rounded half up
        self._uow.reviews.add(
            NewReview(
                booking_id=booking.id,
                listing_id=booking.listing_id,
                author_id=guest.id,
                rating=overall,
                cleanliness=data.cleanliness,
                accuracy=data.accuracy,
                check_in=data.check_in,
                communication=data.communication,
                location=data.location,
                value=data.value,
                comment=data.comment,
                created_at=self._clock.now(),
            )
        )
        self._refresh_superhost(booking.listing_id, today)
        self._uow.commit()

    def _refresh_superhost(self, listing_id: int, today) -> None:
        """Recompute the host's Superhost badge, since a new review changes their average."""
        listing = self._uow.listings.get(listing_id)
        host = self._uow.users.get_by_id(listing.host_id)
        qualifies = qualifies_as_superhost(self._uow.host_reader.superhost_inputs(host.id, today))
        if qualifies != host.is_superhost:
            self._uow.users.update(
                replace(host, is_superhost=qualifies, updated_at=self._clock.now())
            )
            log_event(
                logger, logging.INFO, "host.superhost_changed", host_id=host.id, value=qualifies
            )
