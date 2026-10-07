from datetime import date

from pydantic import BaseModel

from app.domain.enums import BookingStatus, ListingStatus


class HostListingOut(BaseModel):
    id: int
    title: str
    status: ListingStatus
    city: str
    state: str
    price_per_night: int
    photo_url: str | None
    rating_avg: float | None
    review_count: int
    upcoming_reservations: int


class ReservationOut(BaseModel):
    code: str
    status: BookingStatus
    listing_id: int
    listing_title: str
    guest_first_name: str
    guest_last_initial: str
    guest_avatar_url: str | None
    check_in: date
    check_out: date
    nights: int
    guests: int
    total: int
    payout: int  # accommodation + cleaning fee: what the host keeps


class HostStatsOut(BaseModel):
    active_listings: int
    upcoming_reservations: int
    earnings_this_month: int
    earnings_total: int  # completed stays only


class PhotoOrder(BaseModel):
    photo_ids: list[int]
