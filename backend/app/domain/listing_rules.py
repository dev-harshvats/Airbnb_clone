"""Listing vocabulary and the rules that decide badges and publishing."""

from app.domain.entities import HostStats, ListingFields
from app.domain.errors import DomainError, ErrorKind

PROPERTY_TYPES = frozenset(
    {
        "house",
        "flat",
        "guest_house",
        "hotel",
        "villa",
        "cottage",
        "houseboat",
        "cabin",
        "farm_stay",
        "treehouse",
        "heritage_home",
        "tent",
    }
)

MIN_PHOTOS_TO_PUBLISH = 5
MAX_PHOTOS = 30
SUPERHOST_MIN_RATING = 4.8
SUPERHOST_MIN_STAYS = 10
SUPERHOST_MAX_CANCELLATION_RATE = 0.01
FAVOURITE_MIN_RATING = 4.9
FAVOURITE_MIN_REVIEWS = 5


def qualifies_as_superhost(stats: HostStats) -> bool:
    if stats.avg_rating is None or stats.completed_stays < SUPERHOST_MIN_STAYS:
        return False
    cancellation_rate = (
        stats.cancelled_bookings / stats.total_bookings if stats.total_bookings else 0
    )
    return (
        stats.avg_rating >= SUPERHOST_MIN_RATING
        and cancellation_rate < SUPERHOST_MAX_CANCELLATION_RATE
    )


def is_guest_favourite(rating_avg: float | None, review_count: int) -> bool:
    return (
        rating_avg is not None
        and rating_avg >= FAVOURITE_MIN_RATING
        and review_count >= FAVOURITE_MIN_REVIEWS
    )


def ensure_publishable(photo_count: int) -> None:
    if photo_count < MIN_PHOTOS_TO_PUBLISH:
        raise DomainError(
            ErrorKind.BAD_REQUEST,
            "NEEDS_MORE_PHOTOS",
            f"Add at least {MIN_PHOTOS_TO_PUBLISH} photos before publishing.",
        )


def validate_listing_fields(fields: ListingFields) -> None:
    """Cross-field rules a single field's range check cannot express."""
    if fields.property_type not in PROPERTY_TYPES:
        raise DomainError(
            ErrorKind.UNPROCESSABLE,
            "INVALID_PROPERTY_TYPE",
            f"Unknown property type: {fields.property_type}",
        )
    if fields.max_nights < fields.min_nights:
        raise DomainError(
            ErrorKind.UNPROCESSABLE,
            "INVALID_NIGHTS",
            "Maximum nights cannot be below minimum nights.",
        )
