"""The database itself must refuse invalid data, whatever the application does."""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.adapters.sql.models import (
    AmenityModel,
    BookingModel,
    CategoryModel,
    ListingAmenityModel,
    ListingModel,
    ListingPhotoModel,
    ReviewModel,
    UserModel,
    WishlistItemModel,
    WishlistModel,
)


@pytest.fixture
def session(app):
    with app.state.session_factory() as s:
        yield s


def make_user(session, email="host@example.com", **kw):
    row = UserModel(
        email=email,
        password_hash="x",
        first_name="Host",
        last_name="One",
        date_of_birth=date(1990, 1, 1),
        **kw,
    )
    session.add(row)
    session.flush()
    return row


def make_listing(session, host, category, **kw):
    fields = {
        "host_id": host.id,
        "category_id": category.id,
        "title": "Sea-facing villa",
        "description": "Lovely",
        "property_type": "villa",
        "place_type": "entire",
        "address_line": "1 Beach Rd",
        "city": "Goa",
        "state": "Goa",
        "postal_code": "403001",
        "latitude": 15.5,
        "longitude": 73.8,
        "price_per_night": 5000,
        "cleaning_fee": 500,
        "max_guests": 4,
        "bedrooms": 2,
        "beds": 2,
        "bathrooms": 1.5,
    } | kw
    row = ListingModel(**fields)
    session.add(row)
    session.flush()
    return row


def make_booking(session, listing, guest, **kw):
    fields = {
        "code": "ABC123XYZ0",
        "listing_id": listing.id,
        "guest_id": guest.id,
        "check_in": date(2026, 11, 1),
        "check_out": date(2026, 11, 4),
        "adults": 2,
        "nightly_rate": 5000,
        "nights": 3,
        "subtotal": 15000,
        "cleaning_fee": 500,
        "service_fee": 2100,
        "taxes": 1860,
        "total": 19460,
        "payment_method_mock": "card",
    } | kw
    row = BookingModel(**fields)
    session.add(row)
    session.flush()
    return row


@pytest.fixture
def world(session):
    category = CategoryModel(slug="beachfront", label="Beachfront", icon_key="beach", sort_order=1)
    session.add(category)
    host = make_user(session)
    guest = make_user(session, "guest@example.com")
    listing = make_listing(session, host, category)
    session.commit()
    return {"category": category, "host": host, "guest": guest, "listing": listing}


def assert_rejected(session, fn):
    with pytest.raises(IntegrityError):
        fn()
        session.flush()
    session.rollback()


def test_defaults_are_applied(session, world):
    listing = world["listing"]
    session.refresh(listing)
    assert listing.status == "draft"
    assert listing.country == "India"
    assert listing.min_nights == 1
    assert listing.created_at.tzinfo is not None
    assert world["host"].is_host is False


def test_emails_are_unique(session, world):
    assert_rejected(
        session,
        lambda: session.add(
            UserModel(
                email="host@example.com",
                password_hash="x",
                first_name="a",
                last_name="b",
                date_of_birth=date(1990, 1, 1),
            )
        ),
    )


@pytest.mark.parametrize(
    "bad",
    [
        {"price_per_night": 0},
        {"price_per_night": -5},
        {"max_guests": 0},
        {"cleaning_fee": -1},
        {"min_nights": 0},
        {"min_nights": 5, "max_nights": 2},
        {"latitude": 91},
        {"longitude": -181},
    ],
)
def test_listing_check_constraints(session, world, bad):
    assert_rejected(session, lambda: make_listing(session, world["host"], world["category"], **bad))


@pytest.mark.parametrize(
    ("table", "column", "bad_value"),
    [
        ("listings", "place_type", "castle"),
        ("listings", "status", "deleted"),
        ("bookings", "status", "pending"),
        ("bookings", "payment_method_mock", "bitcoin"),
    ],
)
def test_enum_columns_are_constrained_by_the_database_itself(
    session, world, table, column, bad_value
):
    """Raw SQL on purpose: the ORM would reject these in Python, but other writers (scripts,
    the sqlite shell, future code) must be refused by the database too."""
    make_booking(session, world["listing"], world["guest"])
    session.commit()
    assert_rejected(
        session,
        lambda: session.execute(
            text(f"UPDATE {table} SET {column} = :v"),  # noqa: S608 (test-only identifiers)
            {"v": bad_value},
        ),
    )


def test_listing_requires_existing_host_and_category(session, world):
    assert_rejected(
        session, lambda: make_listing(session, world["host"], world["category"], host_id=999)
    )
    assert_rejected(
        session, lambda: make_listing(session, world["host"], world["category"], category_id=999)
    )


def test_booking_dates_must_be_ordered(session, world):
    same_day = {"check_in": date(2026, 11, 1), "check_out": date(2026, 11, 1)}
    backwards = {"check_in": date(2026, 11, 5), "check_out": date(2026, 11, 1)}
    for bad in (same_day, backwards):
        assert_rejected(
            session, lambda bad=bad: make_booking(session, world["listing"], world["guest"], **bad)
        )


@pytest.mark.parametrize("bad", [{"nights": 0}, {"adults": 0}, {"total": -1}])
def test_booking_check_constraints(session, world, bad):
    assert_rejected(session, lambda: make_booking(session, world["listing"], world["guest"], **bad))


def test_booking_codes_are_unique(session, world):
    make_booking(session, world["listing"], world["guest"])
    assert_rejected(
        session,
        lambda: make_booking(
            session,
            world["listing"],
            world["guest"],
            check_in=date(2026, 12, 1),
            check_out=date(2026, 12, 3),
        ),
    )


def test_idempotency_key_is_unique_per_guest_but_nulls_repeat(session, world):
    make_booking(session, world["listing"], world["guest"], code="CODE000001", idempotency_key=None)
    make_booking(session, world["listing"], world["guest"], code="CODE000002", idempotency_key=None)
    make_booking(session, world["listing"], world["guest"], code="CODE000003", idempotency_key="k1")
    assert_rejected(
        session,
        lambda: make_booking(
            session, world["listing"], world["guest"], code="CODE000004", idempotency_key="k1"
        ),
    )
    # another guest may reuse the same key
    make_booking(session, world["listing"], world["host"], code="CODE000005", idempotency_key="k1")


def test_bookings_are_records_and_block_deleting_their_listing(session, world):
    make_booking(session, world["listing"], world["guest"])
    session.commit()
    assert_rejected(session, lambda: session.delete(world["listing"]))


def test_a_booking_blocks_deleting_its_guest(session, world):
    make_booking(session, world["listing"], world["guest"])
    session.commit()
    assert_rejected(session, lambda: session.delete(world["guest"]))


def test_one_review_per_booking_and_ratings_between_1_and_5(session, world):
    booking = make_booking(session, world["listing"], world["guest"])
    ratings = dict(
        rating=5, cleanliness=5, accuracy=5, check_in=5, communication=5, location=5, value=5
    )

    def review(**kw):
        session.add(
            ReviewModel(
                booking_id=booking.id,
                listing_id=world["listing"].id,
                author_id=world["guest"].id,
                comment="Great",
                **(ratings | kw),
            )
        )
        session.flush()

    assert_rejected(session, lambda: review(rating=6))
    assert_rejected(session, lambda: review(cleanliness=0))
    booking = session.merge(booking)
    review()
    assert_rejected(session, review)  # a second review of the same stay


def test_deleting_a_never_booked_listing_cascades_photos_amenities_and_wishlist_items(
    session, world
):
    listing = world["listing"]
    wifi = AmenityModel(key="wifi", name="Wifi", icon_key="wifi", group="essentials")
    session.add(wifi)
    session.flush()
    session.add_all(
        [
            ListingPhotoModel(
                listing_id=listing.id,
                url="/media/1.webp",
                card_url="/media/1_card.webp",
                position=0,
            ),
            ListingAmenityModel(listing_id=listing.id, amenity_id=wifi.id),
        ]
    )
    wishlist = WishlistModel(user_id=world["guest"].id, name="Goa")
    session.add(wishlist)
    session.flush()
    session.add(WishlistItemModel(wishlist_id=wishlist.id, listing_id=listing.id))
    session.commit()

    session.execute(ListingModel.__table__.delete().where(ListingModel.id == listing.id))
    session.commit()
    for model in (ListingPhotoModel, ListingAmenityModel, WishlistItemModel):
        assert session.query(model).count() == 0
    assert session.query(AmenityModel).count() == 1  # reference data is kept


def test_photo_positions_are_unique_per_listing(session, world):
    listing = world["listing"]
    session.add(
        ListingPhotoModel(listing_id=listing.id, url="/a.webp", card_url="/a_c.webp", position=0)
    )
    session.flush()
    assert_rejected(
        session,
        lambda: session.add(
            ListingPhotoModel(
                listing_id=listing.id, url="/b.webp", card_url="/b_c.webp", position=0
            )
        ),
    )


def test_wishlist_names_are_unique_per_user_and_items_are_not_duplicated(session, world):
    session.add(WishlistModel(user_id=world["guest"].id, name="Trip"))
    session.flush()
    assert_rejected(
        session, lambda: session.add(WishlistModel(user_id=world["guest"].id, name="Trip"))
    )

    wishlist = WishlistModel(user_id=world["guest"].id, name="Other")
    session.add(wishlist)
    session.flush()
    session.add(WishlistItemModel(wishlist_id=wishlist.id, listing_id=world["listing"].id))
    session.flush()
    assert_rejected(
        session,
        lambda: session.add(
            WishlistItemModel(wishlist_id=wishlist.id, listing_id=world["listing"].id)
        ),
    )


def test_amenity_group_is_constrained(session):
    assert_rejected(
        session,
        lambda: session.execute(
            text(
                'INSERT INTO amenities (key, name, icon_key, "group") '
                "VALUES ('x', 'X', 'x', 'bogus')"
            )
        ),
    )
