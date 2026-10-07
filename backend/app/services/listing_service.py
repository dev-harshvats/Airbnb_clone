from collections.abc import Sequence
from datetime import date, timedelta

from app.domain.booking_policy import validate_stay
from app.domain.entities import Listing, User
from app.domain.enums import ListingStatus
from app.domain.errors import DomainError, ErrorKind
from app.domain.pricing import FeeRule, calculate_quote
from app.ports.clock import Clock
from app.ports.uow import UnitOfWork
from app.schemas.common import Page
from app.schemas.listing import AvailabilityOut, DateRange, ListingDetailOut, QuoteOut
from app.schemas.review import ReviewOut

AVAILABILITY_WINDOW_DAYS = 365


def listing_not_found() -> DomainError:
    return DomainError(ErrorKind.NOT_FOUND, "LISTING_NOT_FOUND", "Listing not found.")


class ListingService:
    """One listing: its detail page, availability calendar, price quote and reviews."""

    def __init__(self, uow: UnitOfWork, clock: Clock, fee_rules: Sequence[FeeRule]) -> None:
        self._uow = uow
        self._clock = clock
        self._fee_rules = fee_rules

    def detail(self, listing_id: int, viewer: User | None) -> ListingDetailOut:
        detail = self._uow.listing_reader.get_detail(listing_id)
        is_owner = viewer is not None and detail is not None and viewer.id == detail.host.id
        # Unpublished listings are invisible to everyone except their host.
        if detail is None or (detail.status != ListingStatus.ACTIVE and not is_owner):
            raise listing_not_found()
        if not is_owner:  # the exact address is only for the host
            detail = detail.model_copy(update={"address_line": None, "postal_code": None})
        return detail

    def availability(
        self, listing_id: int, start: date | None, end: date | None
    ) -> AvailabilityOut:
        self._public_listing(listing_id)
        start = start or self._clock.today()
        end = end or start + timedelta(days=AVAILABILITY_WINDOW_DAYS)
        ranges = self._uow.bookings.booked_ranges(listing_id, start, end)
        return AvailabilityOut(booked=[DateRange(check_in=a, check_out=b) for a, b in ranges])

    def quote(self, listing_id: int, check_in: date, check_out: date) -> QuoteOut:
        listing = self._public_listing(listing_id)
        nights = validate_stay(listing, check_in, check_out, self._clock.today())
        if self._uow.bookings.has_overlap(listing_id, check_in, check_out):
            raise DomainError(
                ErrorKind.CONFLICT, "BOOKING_CONFLICT", "Those dates are no longer available."
            )
        quote = calculate_quote(
            listing.price_per_night, listing.cleaning_fee, nights, self._fee_rules
        )
        return QuoteOut(**{k: getattr(quote, k) for k in QuoteOut.model_fields})

    def reviews(self, listing_id: int, page: int, page_size: int) -> Page[ReviewOut]:
        self._public_listing(listing_id)
        return self._uow.reviews.list_for_listing(listing_id, page, page_size)

    def _public_listing(self, listing_id: int) -> Listing:
        listing = self._uow.listings.get(listing_id)
        if listing is None or listing.status != ListingStatus.ACTIVE:
            raise listing_not_found()
        return listing
