"""Plain, immutable domain entities. They know nothing about SQL, HTTP or JSON."""

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import BookingStatus, ListingStatus, PaymentMethod, PlaceType


@dataclass(frozen=True, slots=True)
class NewUser:
    email: str
    password_hash: str
    first_name: str
    last_name: str
    date_of_birth: date
    avatar_url: str | None
    bio: str | None
    is_host: bool
    is_superhost: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class User:
    id: int
    email: str
    password_hash: str
    first_name: str
    last_name: str
    date_of_birth: date
    avatar_url: str | None
    bio: str | None
    is_host: bool
    is_superhost: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewRefreshToken:
    user_id: int
    token_hash: str
    family_id: str
    expires_at: datetime
    user_agent: str | None
    ip: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RefreshToken:
    id: int
    user_id: int
    token_hash: str
    family_id: str
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by_id: int | None
    user_agent: str | None
    ip: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ClientInfo:
    """Who is calling, recorded against refresh tokens for auditing."""

    ip: str | None
    user_agent: str | None


@dataclass(frozen=True, slots=True)
class AuthSession:
    """Everything the API needs to answer a successful sign-up, login or refresh."""

    user: User
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime


@dataclass(frozen=True, slots=True)
class ListingFields:
    """What a host can edit on a listing."""

    category_id: int
    title: str
    description: str
    property_type: str
    place_type: PlaceType
    address_line: str
    city: str
    state: str
    country: str
    postal_code: str
    latitude: float
    longitude: float
    price_per_night: int
    cleaning_fee: int
    min_nights: int
    max_nights: int
    max_guests: int
    bedrooms: int
    beds: int
    bathrooms: float
    pets_allowed: bool
    house_rules: str
    check_in_time: str
    check_out_time: str


@dataclass(frozen=True, slots=True)
class Listing(ListingFields):
    id: int
    host_id: int
    status: ListingStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewBooking:
    code: str
    listing_id: int
    guest_id: int
    check_in: date
    check_out: date
    adults: int
    children: int
    infants: int
    pets: int
    nightly_rate: int
    nights: int
    subtotal: int
    cleaning_fee: int
    service_fee: int
    taxes: int
    total: int
    payment_method: PaymentMethod
    idempotency_key: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Booking(NewBooking):
    id: int
    status: BookingStatus
    cancelled_at: datetime | None


@dataclass(frozen=True, slots=True)
class NewReview:
    booking_id: int
    listing_id: int
    author_id: int
    rating: int
    cleanliness: int
    accuracy: int
    check_in: int
    communication: int
    location: int
    value: int
    comment: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Review(NewReview):
    id: int


@dataclass(frozen=True, slots=True)
class Wishlist:
    id: int
    user_id: int
    name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class HostStats:
    """Inputs to the Superhost rule."""

    avg_rating: float | None
    completed_stays: int
    total_bookings: int
    cancelled_bookings: int
