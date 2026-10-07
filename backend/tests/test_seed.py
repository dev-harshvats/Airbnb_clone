from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.adapters.sql.models import (
    BookingModel,
    ExperienceModel,
    ListingModel,
    ListingPhotoModel,
    ReviewModel,
    ServiceModel,
    UserModel,
)
from app.seed.destinations import DESTINATIONS
from app.seed.runner import seed_database

BACKEND = Path(__file__).resolve().parent.parent
TODAY = date(2026, 10, 7)


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    """Seed once for the whole module: bcrypt makes seeding the slowest thing in the suite."""
    from app.core.config import Settings
    from tests.conftest import TEST_NOW, build_app
    from tests.fakes.clock import FixedClock

    tmp = tmp_path_factory.mktemp("seed")
    settings = Settings(
        _env_file=None,
        ENV="test",
        DATABASE_URL=f"sqlite:///{tmp / 'seed.db'}",
        MEDIA_DIR=tmp / "media",
        JWT_SECRET="seed-test-secret-seed-test-secret-0123456789",
        BCRYPT_ROUNDS=4,
    )
    app = build_app(settings, FixedClock(TEST_NOW))
    with app.state.session_factory() as session:
        created = seed_database(
            session, tmp / "media", TODAY, TEST_NOW, photos_dir=BACKEND / "media"
        )
    return {"app": app, "created": created, "settings": settings, "tmp": tmp}


def count(app, model):
    with app.state.session_factory() as s:
        return s.scalar(select(func.count()).select_from(model))


def test_seed_builds_a_realistic_indian_marketplace(seeded):
    app = seeded["app"]
    assert seeded["created"] is True
    with app.state.session_factory() as s:
        users = s.scalars(select(UserModel)).all()
        listings = s.scalars(select(ListingModel)).all()
        bookings = s.scalars(select(BookingModel)).all()
        reviews = s.scalars(select(ReviewModel)).all()

        assert len(users) == 10 and sum(u.is_host for u in users) == 6
        assert {u.first_name for u in users if u.is_superhost} == {
            "Aarav",
            "Priya",
        }  # earned, not assigned
        assert len(listings) >= 55 and all(row.country == "India" for row in listings)
        known = {(d.city, d.state) for d in DESTINATIONS}
        assert {(row.city, row.state) for row in listings} <= known
        assert all(1800 <= row.price_per_night <= 45000 for row in listings)
        assert len(bookings) >= 70 and any(b.status == "cancelled" for b in bookings)

        # a confirmed stay never overlaps another confirmed stay on the same listing
        stays = [b for b in bookings if b.status == "confirmed"]
        for i, a in enumerate(stays):
            for b in stays[i + 1 :]:
                if a.listing_id == b.listing_id:
                    assert not (a.check_in < b.check_out and a.check_out > b.check_in)

        # reviews only exist for stays that are over
        by_id = {b.id: b for b in bookings}
        assert reviews and len({r.booking_id for r in reviews}) == len(reviews)
        assert all(by_id[r.booking_id].status == "confirmed" for r in reviews)
        assert all(by_id[r.booking_id].check_out < TODAY for r in reviews)


def test_every_listing_has_five_photos_that_exist_on_disk(seeded):
    app = seeded["app"]
    with app.state.session_factory() as s:
        photos = s.scalars(select(ListingPhotoModel)).all()
        per_listing = {}
        for photo in photos:
            per_listing[photo.listing_id] = per_listing.get(photo.listing_id, 0) + 1
            for url in (photo.url, photo.card_url):
                assert (BACKEND / url.removeprefix("/")).is_file(), url
    assert set(per_listing.values()) == {5}


def test_demo_accounts_and_badges_work_through_the_api(seeded):
    from fastapi.testclient import TestClient

    with TestClient(seeded["app"]) as client:
        for email in ("guest@example.com", "host@example.com"):
            res = client.post(
                "/api/v1/auth/login", json={"email": email, "password": "Password123"}
            )
            assert res.status_code == 200, email
        page = client.get("/api/v1/listings", params={"page_size": 50}).json()
        assert page["total"] >= 55 and page["items"][0]["photos"]  # (one demo listing is unlisted)
        assert any(card["is_guest_favourite"] for card in page["items"])
        assert any(card["host_is_superhost"] for card in page["items"])
        goa = client.get("/api/v1/listings", params={"location": "goa"}).json()
        assert goa["total"] >= 5
        assert len(client.get("/api/v1/categories").json()) >= 12


def test_seeding_twice_changes_nothing_and_reset_rebuilds_the_same_data(seeded):
    app, tmp = seeded["app"], seeded["tmp"]
    before = (count(app, UserModel), count(app, ListingModel), count(app, BookingModel))
    with app.state.session_factory() as s:
        from tests.conftest import TEST_NOW

        assert (
            seed_database(s, tmp / "media", TODAY, TEST_NOW, photos_dir=BACKEND / "media") is False
        )
        assert (
            seed_database(
                s, tmp / "media", TODAY, TEST_NOW, reset=True, photos_dir=BACKEND / "media"
            )
            is True
        )
    assert (count(app, UserModel), count(app, ListingModel), count(app, BookingModel)) == before


def test_the_experiences_and_services_tabs_have_content(seeded):
    app = seeded["app"]
    assert count(app, ExperienceModel) >= 20 and count(app, ServiceModel) >= 15
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        assert client.get("/api/v1/experiences").json()["total"] >= 20
        assert len(client.get("/api/v1/services/types").json()) == 6
