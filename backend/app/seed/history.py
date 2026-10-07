"""Bookings, reviews and wishlists, generated relative to today so the demo always looks current.

Dates are laid out sequentially per listing (past stays, then upcoming ones), so confirmed bookings
never overlap. Cancelled bookings may overlap anything because they do not block dates."""

import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.adapters.sql.models import (
    BookingModel,
    ReviewModel,
    UserModel,
    WishlistItemModel,
    WishlistModel,
)
from app.domain.codes import generate_booking_code
from app.domain.pricing import calculate_quote, default_rules
from app.seed.builder import ListingInfo
from app.seed.content import REVIEW_COMMENTS

SUPERHOST_KEYS = {"aarav", "priya"}  # these hosts get many 5-star stays, so they earn the badge
STAR_LISTINGS_PER_SUPERHOST = 3  # listings with enough 5-star reviews to be "Guest favourite"
RULES = default_rules(service_fee_rate=0.14, tax_rate=0.12)


def _stay(
    rng: random.Random, info: ListingInfo, guest: UserModel, start: date, nights: int,
    status: str, now: datetime, used_codes: set[str],
) -> BookingModel:  # fmt: skip
    quote = calculate_quote(info.price, info.cleaning_fee, nights, RULES)
    code = generate_booking_code()
    while code in used_codes:
        code = generate_booking_code()
    used_codes.add(code)
    adults = rng.randint(1, min(info.max_guests, 4))
    booked_at = min(
        now, datetime.combine(start - timedelta(days=rng.randint(10, 60)), now.timetz())
    )
    return BookingModel(
        code=code, listing_id=info.id, guest_id=guest.id, check_in=start,
        check_out=start + timedelta(days=nights), adults=adults,
        children=rng.choice([0, 0, 0, 1]) if info.max_guests > adults else 0,
        infants=0, pets=1 if info.pets_allowed and rng.random() < 0.15 else 0,
        nightly_rate=quote.nightly_rate, nights=nights, subtotal=quote.subtotal,
        cleaning_fee=quote.cleaning_fee, service_fee=quote.service_fee, taxes=quote.taxes,
        total=quote.total, status=status, payment_method_mock=rng.choice(["card", "upi"]),
        created_at=booked_at, cancelled_at=booked_at + timedelta(days=2) if status == "cancelled" else None,
    )  # fmt: skip


def _review(rng: random.Random, booking: BookingModel, rating: int, now: datetime) -> ReviewModel:
    def around() -> int:  # category scores stay close to the overall rating
        return max(1, min(5, rating + rng.choice([0, 0, 0, -1 if rating > 3 else 1])))

    posted = datetime.combine(booking.check_out + timedelta(days=rng.randint(1, 4)), now.timetz())
    return ReviewModel(
        booking_id=booking.id, listing_id=booking.listing_id, author_id=booking.guest_id,
        rating=rating, cleanliness=around(), accuracy=around(), check_in=around(),
        communication=around(), location=around(), value=around(),
        comment=rng.choice(REVIEW_COMMENTS[rating]), created_at=min(now, posted),
    )  # fmt: skip


def create_history(
    session: Session, rng: random.Random, listings: list[ListingInfo],
    guests: list[UserModel], today: date, now: datetime,
) -> None:  # fmt: skip
    used_codes: set[str] = set()
    stars: set[int] = set()
    for key in SUPERHOST_KEYS:
        stars.update([i.id for i in listings if i.host_key == key][:STAR_LISTINGS_PER_SUPERHOST])

    for info in listings:
        superhost = info.host_key in SUPERHOST_KEYS
        star = info.id in stars
        completed = (
            rng.randint(6, 8)
            if star
            else rng.randint(2, 4)
            if superhost
            else rng.choices([0, 1, 2, 3], weights=[30, 35, 25, 10])[0]
        )
        upcoming = rng.choices([0, 1, 2], weights=[45, 40, 15])[0]
        bookings: list[BookingModel] = []

        end = today - timedelta(days=rng.randint(3, 12))
        for _ in range(completed):  # walk backwards from today
            nights = max(info.min_nights, rng.randint(2, 5))
            start = end - timedelta(days=nights)
            if (today - start).days > 440:
                break
            bookings.append(
                _stay(rng, info, rng.choice(guests), start, nights, "confirmed", now, used_codes)
            )
            end = start - timedelta(days=rng.randint(4, 30))

        cursor = today + timedelta(days=rng.randint(3, 25))
        for _ in range(upcoming):  # then walk forwards
            nights = max(info.min_nights, rng.randint(2, 5))
            bookings.append(
                _stay(rng, info, rng.choice(guests), cursor, nights, "confirmed", now, used_codes)
            )
            cursor += timedelta(days=nights + rng.randint(3, 25))

        if not superhost and rng.random() < 0.18:  # a cancelled trip; never for the superhosts
            start = today + timedelta(days=rng.randint(30, 90))
            bookings.append(
                _stay(rng, info, rng.choice(guests), start, 3, "cancelled", now, used_codes)
            )

        session.add_all(bookings)
        session.flush()

        for booking in bookings:
            if booking.status == "confirmed" and booking.check_out < today and rng.random() < 0.92:
                if superhost:
                    rating = 5 if star or rng.random() < 0.96 else 4
                else:
                    rating = rng.choices([5, 4, 3, 2], weights=[48, 36, 12, 4])[0]
                session.add(_review(rng, booking, rating, now))
    session.flush()


def create_wishlists(session: Session, rng: random.Random, guests: list[UserModel],
                     listing_ids: list[int], now: datetime) -> None:  # fmt: skip
    for guest in guests:
        for name in rng.sample(
            ["Weekend getaways", "Dream stays", "Family trip", "Mountains", "By the sea"], k=2
        ):
            wishlist = WishlistModel(
                user_id=guest.id, name=name, created_at=now - timedelta(days=rng.randint(5, 90))
            )
            session.add(wishlist)
            session.flush()
            for listing_id in rng.sample(listing_ids, k=rng.randint(2, 4)):
                session.add(
                    WishlistItemModel(
                        wishlist_id=wishlist.id, listing_id=listing_id, created_at=now
                    )
                )
    session.flush()
