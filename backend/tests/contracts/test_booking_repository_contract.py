"""Both BookingRepository implementations must agree on availability (Liskov)."""

from datetime import UTC, date, datetime

import pytest

from app.adapters.sql.models import CategoryModel, ListingModel, UserModel
from app.adapters.sql.uow import SqlUnitOfWork
from app.core.database import Base, build_engine, build_session_factory
from app.domain.entities import NewBooking
from app.domain.enums import PaymentMethod

NOW = datetime(2026, 10, 7, 6, 30, tzinfo=UTC)
D = date  # short alias for the calendar below


@pytest.fixture(params=["memory", "sql"])
def repo_and_ids(request, tmp_path):
    """Yields (bookings repository, listing id, guest id)."""
    if request.param == "memory":
        from tests.fakes.uow import InMemoryUnitOfWork

        yield InMemoryUnitOfWork().bookings, 1, 2
        return
    engine = build_engine(f"sqlite:///{tmp_path / 'contract.db'}")
    Base.metadata.create_all(engine)
    with build_session_factory(engine)() as session:
        category = CategoryModel(slug="c", label="C", icon_key="c")
        host = UserModel(
            email="h@x.com",
            password_hash="x",
            first_name="H",
            last_name="H",
            date_of_birth=D(1990, 1, 1),
        )
        guest = UserModel(
            email="g@x.com",
            password_hash="x",
            first_name="G",
            last_name="G",
            date_of_birth=D(1990, 1, 1),
        )
        session.add_all([category, host, guest])
        session.flush()
        listing = ListingModel(
            host_id=host.id, category_id=category.id, title="t", description="d",
            property_type="villa", place_type="entire", address_line="a", city="c", state="s",
            postal_code="123456", latitude=1, longitude=1, price_per_night=1000, max_guests=2,
            bedrooms=1, beds=1, bathrooms=1,
        )  # fmt: skip
        session.add(listing)
        session.flush()
        yield SqlUnitOfWork(session).bookings, listing.id, guest.id
    engine.dispose()


def booking(listing_id, guest_id, check_in, check_out, code="AAAAAAAAAA") -> NewBooking:
    return NewBooking(
        code=code, listing_id=listing_id, guest_id=guest_id, check_in=check_in,
        check_out=check_out, adults=1, children=0, infants=0, pets=0, nightly_rate=1000,
        nights=(check_out - check_in).days, subtotal=1000, cleaning_fee=0, service_fee=0,
        taxes=0, total=1000, payment_method=PaymentMethod.CARD, idempotency_key=None,
        created_at=NOW,
    )  # fmt: skip


def test_overlap_is_half_open(repo_and_ids):
    repo, listing, guest = repo_and_ids
    repo.add(booking(listing, guest, D(2026, 11, 10), D(2026, 11, 13)))

    assert repo.has_overlap(listing, D(2026, 11, 12), D(2026, 11, 14))  # shares one night
    assert repo.has_overlap(listing, D(2026, 11, 11), D(2026, 11, 12))  # inside
    assert repo.has_overlap(listing, D(2026, 11, 9), D(2026, 11, 20))  # swallows it
    assert not repo.has_overlap(
        listing, D(2026, 11, 13), D(2026, 11, 15)
    )  # starts on check-out day
    assert not repo.has_overlap(listing, D(2026, 11, 7), D(2026, 11, 10))  # ends on check-in day
    assert not repo.has_overlap(listing + 99, D(2026, 11, 10), D(2026, 11, 13))  # other listing


def test_cancelled_bookings_free_their_dates_and_ranges_are_sorted(repo_and_ids):
    repo, listing, guest = repo_and_ids
    later = repo.add(booking(listing, guest, D(2026, 12, 1), D(2026, 12, 3), code="BBBBBBBBBB"))
    earlier = repo.add(booking(listing, guest, D(2026, 11, 10), D(2026, 11, 13), code="CCCCCCCCCC"))

    assert repo.booked_ranges(listing, D(2026, 11, 1), D(2026, 12, 31)) == [
        (D(2026, 11, 10), D(2026, 11, 13)),
        (D(2026, 12, 1), D(2026, 12, 3)),
    ]
    repo.mark_cancelled(earlier.id, NOW)
    assert not repo.has_overlap(listing, D(2026, 11, 10), D(2026, 11, 13))
    assert repo.booked_ranges(listing, D(2026, 11, 1), D(2026, 12, 31)) == [
        (D(2026, 12, 1), D(2026, 12, 3))
    ]
    assert later.id != earlier.id
