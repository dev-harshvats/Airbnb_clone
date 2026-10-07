"""Booking rules, and the date arithmetic behind them. Stays are half-open [check_in, check_out):
the guest leaves on check_out, so another stay may start the same day."""

from datetime import date

from app.domain.entities import Booking, Listing
from app.domain.enums import BookingStatus, ListingStatus
from app.domain.errors import DomainError, ErrorKind


def overlaps(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return a_start < b_end and a_end > b_start


def nights_between(check_in: date, check_out: date) -> int:
    return (check_out - check_in).days


def is_completed(booking: Booking, today: date) -> bool:
    """A confirmed stay is completed once the check-out day has passed (not on check-out day)."""
    return booking.status == BookingStatus.CONFIRMED and booking.check_out < today


def is_upcoming(booking: Booking, today: date) -> bool:
    return booking.status == BookingStatus.CONFIRMED and booking.check_out >= today


def _bad(code: str, detail: str) -> DomainError:
    return DomainError(ErrorKind.BAD_REQUEST, code, detail)


def validate_stay(listing: Listing, check_in: date, check_out: date, today: date) -> int:
    """Rules about the dates alone (shared by price quotes and bookings). Returns the nights."""
    if listing.status != ListingStatus.ACTIVE:
        raise _bad("LISTING_UNAVAILABLE", "This listing is not available to book.")
    if check_out <= check_in:
        raise _bad("INVALID_DATES", "Check-out must be after check-in.")
    if check_in < today:
        raise _bad("PAST_DATE", "Check-in cannot be in the past.")
    nights = nights_between(check_in, check_out)
    if nights < listing.min_nights:
        raise _bad("MIN_NIGHTS", f"The minimum stay is {listing.min_nights} nights.")
    if nights > listing.max_nights:
        raise _bad("MAX_NIGHTS", f"The maximum stay is {listing.max_nights} nights.")
    return nights


def validate_booking(
    listing: Listing,
    guest_id: int,
    check_in: date,
    check_out: date,
    adults: int,
    children: int,
    pets: int,
    today: date,
) -> int:
    """Raise a DomainError for the first broken rule; otherwise return the number of nights."""
    if guest_id == listing.host_id:
        raise _bad("OWN_LISTING", "You cannot book your own listing.")
    nights = validate_stay(listing, check_in, check_out, today)
    if adults + children > listing.max_guests:
        raise _bad("TOO_MANY_GUESTS", f"This place sleeps at most {listing.max_guests} guests.")
    if pets > 0 and not listing.pets_allowed:
        raise _bad("PETS_NOT_ALLOWED", "Pets are not allowed at this place.")
    return nights
