"""Insert reference data, listings, bookings and reviews straight into the database."""

import itertools
from datetime import date

from app.adapters.sql.models import (
    AmenityModel,
    BookingModel,
    CategoryModel,
    ListingAmenityModel,
    ListingModel,
    ListingPhotoModel,
    ReviewModel,
)

_codes = itertools.count(1)


class Factory:
    def __init__(self, app, clock) -> None:
        self._app = app
        self._clock = clock

    def _session(self):
        return self._app.state.session_factory()

    def category(self, slug: str = "beachfront") -> int:
        with self._session() as s:
            row = CategoryModel(slug=slug, label=slug.title(), icon_key=slug)
            s.add(row)
            s.commit()
            return row.id

    def amenity(self, key: str, group: str = "essentials") -> int:
        with self._session() as s:
            row = AmenityModel(key=key, name=key.title(), icon_key=key, group=group)
            s.add(row)
            s.commit()
            return row.id

    def listing(
        self, host_id: int, category_id: int, amenity_ids=(), photos: int = 5, **overrides
    ) -> int:
        fields = {
            "host_id": host_id,
            "category_id": category_id,
            "title": "Sea-facing villa",
            "description": "A lovely place to stay.",
            "property_type": "villa",
            "place_type": "entire",
            "address_line": "12 Beach Road",
            "city": "Goa",
            "state": "Goa",
            "postal_code": "403001",
            "latitude": 15.5,
            "longitude": 73.8,
            "price_per_night": 5000,
            "cleaning_fee": 1500,
            "max_guests": 4,
            "bedrooms": 2,
            "beds": 2,
            "bathrooms": 1.5,
            "status": "active",
            "created_at": self._clock.now(),
            "updated_at": self._clock.now(),
        } | overrides
        with self._session() as s:
            row = ListingModel(**fields)
            s.add(row)
            s.flush()
            for i in range(photos):
                s.add(
                    ListingPhotoModel(
                        listing_id=row.id,
                        url=f"/media/seed/{row.id}/{i}.webp",
                        card_url=f"/media/seed/{row.id}/{i}_card.webp",
                        position=i,
                    )
                )
            for amenity_id in amenity_ids:
                s.add(ListingAmenityModel(listing_id=row.id, amenity_id=amenity_id))
            s.commit()
            return row.id

    def booking(
        self,
        listing_id: int,
        guest_id: int,
        check_in: date,
        check_out: date,
        status: str = "confirmed",
        **overrides,
    ) -> int:
        nights = (check_out - check_in).days
        fields = {
            "code": f"TEST{next(_codes):06d}",
            "listing_id": listing_id,
            "guest_id": guest_id,
            "check_in": check_in,
            "check_out": check_out,
            "adults": 2,
            "nightly_rate": 5000,
            "nights": nights,
            "subtotal": 5000 * nights,
            "cleaning_fee": 1500,
            "service_fee": 0,
            "taxes": 0,
            "total": 5000 * nights + 1500,
            "payment_method_mock": "card",
            "status": status,
            "created_at": self._clock.now(),
        } | overrides
        with self._session() as s:
            row = BookingModel(**fields)
            s.add(row)
            s.commit()
            return row.id

    def review(self, booking_id: int, listing_id: int, author_id: int, rating: int = 5) -> None:
        with self._session() as s:
            s.add(
                ReviewModel(
                    booking_id=booking_id,
                    listing_id=listing_id,
                    author_id=author_id,
                    rating=rating,
                    cleanliness=rating,
                    accuracy=rating,
                    check_in=rating,
                    communication=rating,
                    location=rating,
                    value=rating,
                    comment="Lovely stay.",
                    created_at=self._clock.now(),
                )
            )
            s.commit()

    def booking_code(self, booking_id: int) -> str:
        with self._session() as s:
            return s.get(BookingModel, booking_id).code
