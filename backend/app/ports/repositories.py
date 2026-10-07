from datetime import date, datetime
from typing import Protocol

from app.domain.entities import (
    Booking,
    HostStats,
    Listing,
    ListingFields,
    NewBooking,
    NewRefreshToken,
    NewReview,
    NewUser,
    RefreshToken,
    Review,
    User,
    Wishlist,
)
from app.schemas.catalog import (
    CatalogSearchParams,
    ExperienceCardOut,
    ExperienceDetailOut,
    ServiceCardOut,
    ServiceDetailOut,
    ServiceTypeOut,
)
from app.schemas.common import Page
from app.schemas.host import HostListingOut, HostStatsOut, ReservationOut
from app.schemas.listing import (
    AmenityOut,
    CategoryOut,
    DestinationOut,
    ListingCardOut,
    ListingDetailOut,
    ListingSummaryOut,
    LocationSuggestion,
    PhotoOut,
    PriceHistogramOut,
    SearchParams,
)
from app.schemas.review import ReviewOut
from app.schemas.wishlist import WishlistOut

# ---------- accounts ----------


class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User | None: ...

    def get_by_email(self, email: str) -> User | None:
        """`email` is already normalized (see domain.auth_policy.normalize_email)."""

    def add(self, new: NewUser) -> User:
        """Raise DomainError(CONFLICT, "EMAIL_TAKEN") when the email is already registered."""

    def update(self, user: User) -> User: ...


class RefreshTokenStore(Protocol):
    def add(self, new: NewRefreshToken) -> RefreshToken: ...

    def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    def revoke(self, token_id: int, when: datetime, replaced_by_id: int | None = None) -> None: ...

    def revoke_family(self, family_id: str, when: datetime) -> int:
        """Revoke every still-live token of a family; return how many were revoked."""

    def purge_expired(self, before: datetime) -> int:
        """Delete tokens that expired before `before` (never usable again); return how many."""


# ---------- listings ----------


class ListingReader(Protocol):
    """Read-only, public views of listings (search results, detail pages, reference data)."""

    def search(self, params: SearchParams) -> Page[ListingCardOut]: ...

    def price_histogram(self, params: SearchParams) -> PriceHistogramOut: ...

    def get_detail(self, listing_id: int) -> ListingDetailOut | None: ...

    def cards(self, listing_ids: list[int]) -> list[ListingCardOut]:
        """Cards for the given ids, in the same order (missing ids are skipped)."""

    def summaries(self, listing_ids: list[int]) -> dict[int, ListingSummaryOut]: ...

    def categories(self) -> list[CategoryOut]: ...

    def amenities(self) -> list[AmenityOut]: ...

    def suggest_locations(self, query: str, limit: int = 8) -> list[LocationSuggestion]: ...

    def destinations(self, limit: int = 20) -> list[DestinationOut]:
        """Cities with published stays, busiest first."""


class ListingRepository(Protocol):
    """The write side of listings, working with the `Listing` entity."""

    def get(self, listing_id: int) -> Listing | None: ...

    def add(
        self, host_id: int, fields: ListingFields, amenity_ids: list[int], when: datetime
    ) -> Listing:
        """Create a draft. Raise DomainError(BAD_REQUEST, "INVALID_REFERENCE") for an unknown
        category or amenity."""

    def update(self, listing: Listing, amenity_ids: list[int] | None, when: datetime) -> Listing:
        """Persist every field of `listing`; replace its amenities when `amenity_ids` is given."""

    def delete(self, listing_id: int) -> None: ...

    def has_bookings(self, listing_id: int) -> bool:
        """True if the listing was ever booked (confirmed or cancelled, past or future)."""

    def photos(self, listing_id: int) -> list[PhotoOut]: ...

    def add_photo(self, listing_id: int, url: str, card_url: str) -> PhotoOut: ...

    def remove_photo(self, listing_id: int, photo_id: int) -> PhotoOut | None: ...

    def reorder_photos(self, listing_id: int, photo_ids: list[int]) -> None: ...


class HostReader(Protocol):
    """Reporting views for hosts."""

    def listings(self, host_id: int, today: date) -> list[HostListingOut]: ...

    def reservations(self, host_id: int, today: date, scope: str | None) -> list[ReservationOut]:
        """`scope` is "upcoming", "past", "cancelled" or None for everything."""

    def stats(self, host_id: int, today: date) -> HostStatsOut: ...

    def superhost_inputs(self, host_id: int, today: date) -> HostStats: ...


# ---------- bookings, reviews, wishlists ----------


class BookingRepository(Protocol):
    def add(self, new: NewBooking) -> Booking: ...

    def get_by_code(self, code: str) -> Booking | None: ...

    def get_by_idempotency_key(self, guest_id: int, key: str) -> Booking | None: ...

    def has_overlap(self, listing_id: int, check_in: date, check_out: date) -> bool:
        """Is there a confirmed booking overlapping [check_in, check_out)? Back-to-back stays
        (one ends the day the other starts) do not overlap; cancelled bookings never count."""

    def booked_ranges(self, listing_id: int, start: date, end: date) -> list[tuple[date, date]]:
        """Confirmed stays overlapping [start, end), earliest first."""

    def mark_cancelled(self, booking_id: int, when: datetime) -> Booking: ...

    def list_for_guest(self, guest_id: int) -> list[Booking]: ...


class ReviewRepository(Protocol):
    def add(self, new: NewReview) -> Review:
        """Raise DomainError(CONFLICT, "REVIEW_EXISTS") when the stay is already reviewed."""

    def reviewed_booking_ids(self, booking_ids: list[int]) -> set[int]: ...

    def list_for_listing(self, listing_id: int, page: int, page_size: int) -> Page[ReviewOut]: ...


class WishlistRepository(Protocol):
    def create(self, user_id: int, name: str, when: datetime) -> Wishlist:
        """Raise DomainError(CONFLICT, "WISHLIST_EXISTS") for a duplicate name."""

    def get(self, wishlist_id: int, user_id: int) -> Wishlist | None:
        """Only returns the wishlist when it belongs to `user_id`."""

    def list_for_user(self, user_id: int) -> list[WishlistOut]: ...

    def listing_ids(self, wishlist_id: int) -> list[int]: ...

    def saved_listing_ids(self, user_id: int) -> list[int]: ...

    def add_item(self, wishlist_id: int, listing_id: int, when: datetime) -> None:
        """Idempotent. Raise DomainError(NOT_FOUND, "LISTING_NOT_FOUND") for an unknown listing."""

    def remove_item(self, wishlist_id: int, listing_id: int) -> None: ...

    def delete(self, wishlist_id: int) -> None: ...


# ---------- experiences and services (browse-only catalogues) ----------


class ExperienceReader(Protocol):
    def search(self, params: CatalogSearchParams) -> Page[ExperienceCardOut]: ...

    def get_detail(self, experience_id: int) -> ExperienceDetailOut | None: ...


class ServiceReader(Protocol):
    def search(self, params: CatalogSearchParams) -> Page[ServiceCardOut]: ...

    def get_detail(self, service_id: int) -> ServiceDetailOut | None: ...

    def types(self, location: str | None) -> list[ServiceTypeOut]:
        """Service categories that have at least one service (in `location`, when given)."""
