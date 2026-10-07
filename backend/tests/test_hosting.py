import io
from datetime import timedelta
from pathlib import Path

import pytest
from PIL import Image

API = "/api/v1/hosting"

NEW_LISTING = {
    "title": "Hilltop cottage",
    "description": "Quiet and green.",
    "property_type": "cottage",
    "place_type": "entire",
    "address_line": "4 Pine Lane",
    "city": "Manali",
    "state": "Himachal Pradesh",
    "postal_code": "175131",
    "latitude": 32.24,
    "longitude": 77.19,
    "price_per_night": 4500,
    "cleaning_fee": 500,
    "max_guests": 4,
    "bedrooms": 2,
    "beds": 3,
    "bathrooms": 1,
}


def png(width=2000, height=1500) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), "teal").save(out, format="PNG")
    return out.getvalue()


@pytest.fixture
def host(make_user, factory):
    user, token = make_user(is_host=True)
    return {
        "user": user,
        "headers": {"Authorization": f"Bearer {token}"},
        "category": factory.category(),
    }


def upload(client, host, listing_id, data=None, name="photo.png"):
    files = {"file": (name, data if data is not None else png(), "image/png")}
    return client.post(f"{API}/listings/{listing_id}/photos", files=files, headers=host["headers"])


def test_only_hosts_can_create_listings(client, make_user, host):
    _, guest_token = make_user()
    body = NEW_LISTING | {"category_id": host["category"]}
    res = client.post(
        f"{API}/listings", json=body, headers={"Authorization": f"Bearer {guest_token}"}
    )
    assert (res.status_code, res.json()["code"]) == (403, "NOT_HOST")


def test_listing_lifecycle_create_photos_publish_edit_and_delete(client, host, settings):
    body = NEW_LISTING | {"category_id": host["category"]}
    created = client.post(f"{API}/listings", json=body, headers=host["headers"])
    assert created.status_code == 201
    listing = created.json()
    listing_id = listing["id"]
    assert listing["status"] == "draft" and listing["address_line"] == "4 Pine Lane"

    # a draft is not searchable and cannot be published without enough photos
    assert client.get("/api/v1/listings").json()["total"] == 0
    publish = client.patch(
        f"{API}/listings/{listing_id}", json={"status": "active"}, headers=host["headers"]
    )
    assert (publish.status_code, publish.json()["code"]) == (400, "NEEDS_MORE_PHOTOS")

    photos = [upload(client, host, listing_id).json() for _ in range(5)]
    uploads = Path(settings.MEDIA_DIR) / "uploads"
    with (
        Image.open(uploads / Path(photos[0]["url"]).name) as full,
        Image.open(uploads / Path(photos[0]["card_url"]).name) as card,
    ):
        assert (full.format, full.width, card.width) == ("WEBP", 1440, 720)

    live = client.patch(
        f"{API}/listings/{listing_id}",
        json={"status": "active", "price_per_night": 4800, "title": "Hilltop cottage with a view"},
        headers=host["headers"],
    )
    assert live.status_code == 200 and live.json()["status"] == "active"
    found = client.get("/api/v1/listings", params={"location": "manali"}).json()
    assert [(i["id"], i["price_per_night"]) for i in found["items"]] == [(listing_id, 4800)]

    # photos can be reordered, but a live listing must keep at least five
    order = [p["id"] for p in reversed(photos)]
    reordered = client.put(
        f"{API}/listings/{listing_id}/photos/order",
        json={"photo_ids": order},
        headers=host["headers"],
    )
    assert [p["id"] for p in reordered.json()] == order
    bad_order = client.put(
        f"{API}/listings/{listing_id}/photos/order",
        json={"photo_ids": order[:2]},
        headers=host["headers"],
    )
    assert bad_order.json()["code"] == "INVALID_PHOTO_ORDER"
    too_few = client.delete(
        f"{API}/listings/{listing_id}/photos/{photos[0]['id']}", headers=host["headers"]
    )
    assert (too_few.status_code, too_few.json()["code"]) == (400, "NEEDS_MORE_PHOTOS")

    # a never-booked listing can be deleted, and its image files go with it
    assert client.delete(f"{API}/listings/{listing_id}", headers=host["headers"]).status_code == 204
    assert client.get(f"/api/v1/listings/{listing_id}").status_code == 404
    assert list(uploads.iterdir()) == []


def test_invalid_input_is_rejected(client, host):
    headers, category = host["headers"], host["category"]
    bad_type = NEW_LISTING | {"category_id": category, "property_type": "castle"}
    assert (
        client.post(f"{API}/listings", json=bad_type, headers=headers).json()["code"]
        == "INVALID_PROPERTY_TYPE"
    )
    bad_category = NEW_LISTING | {"category_id": 9999}
    assert (
        client.post(f"{API}/listings", json=bad_category, headers=headers).json()["code"]
        == "INVALID_REFERENCE"
    )
    free = NEW_LISTING | {"category_id": category, "price_per_night": 0}
    assert client.post(f"{API}/listings", json=free, headers=headers).status_code == 422


def test_uploading_something_that_is_not_an_image_is_refused(client, host, factory):
    listing = factory.listing(host["user"].id, host["category"])
    res = upload(client, host, listing, data=b"definitely not an image", name="notes.png")
    assert (res.status_code, res.json()["code"]) == (400, "INVALID_IMAGE")


def test_other_hosts_cannot_touch_my_listing(client, make_user, host, factory):
    listing = factory.listing(host["user"].id, host["category"])
    _, other_token = make_user(is_host=True)
    other = {"Authorization": f"Bearer {other_token}"}
    for res in (
        client.patch(f"{API}/listings/{listing}", json={"title": "Mine now"}, headers=other),
        client.delete(f"{API}/listings/{listing}", headers=other),
    ):
        assert (res.status_code, res.json()["code"]) == (403, "NOT_OWNER")
    assert client.patch(f"{API}/listings/9999", json={}, headers=other).status_code == 404


def test_a_listing_that_was_ever_booked_cannot_be_deleted_only_unlisted(
    client, host, factory, make_user, clock
):
    guest, _ = make_user()
    today = clock.today()
    upcoming = factory.listing(host["user"].id, host["category"])
    past_only = factory.listing(host["user"].id, host["category"])
    factory.booking(upcoming, guest.id, today + timedelta(days=5), today + timedelta(days=7))
    factory.booking(past_only, guest.id, today - timedelta(days=9), today - timedelta(days=7))

    for listing_id in (upcoming, past_only):
        res = client.delete(f"{API}/listings/{listing_id}", headers=host["headers"])
        assert (res.status_code, res.json()["code"]) == (409, "LISTING_HAS_BOOKINGS")

    unlisted = client.patch(
        f"{API}/listings/{upcoming}", json={"status": "inactive"}, headers=host["headers"]
    )
    assert unlisted.json()["status"] == "inactive"
    assert client.get(f"/api/v1/listings/{upcoming}").status_code == 404  # hidden from guests


def test_dashboard_lists_my_listings_reservations_and_earnings(
    client, host, factory, make_user, clock
):
    guest, _ = make_user()
    rival, rival_token = make_user(is_host=True)
    today = clock.today()
    mine = factory.listing(host["user"].id, host["category"], title="Mine")
    theirs = factory.listing(rival.id, factory.category("other"), title="Theirs")
    soon = factory.booking(mine, guest.id, today + timedelta(days=3), today + timedelta(days=5))
    factory.booking(mine, guest.id, today - timedelta(days=9), today - timedelta(days=7))
    factory.booking(
        mine, guest.id, today + timedelta(days=20), today + timedelta(days=22), status="cancelled"
    )
    factory.booking(theirs, guest.id, today + timedelta(days=3), today + timedelta(days=5))

    listings = client.get(f"{API}/listings", headers=host["headers"]).json()
    assert [(item["title"], item["upcoming_reservations"]) for item in listings] == [("Mine", 1)]

    def reservations(**params):
        return client.get(f"{API}/reservations", params=params, headers=host["headers"]).json()

    assert len(reservations()) == 3  # never someone else's bookings
    assert [r["code"] for r in reservations(status="upcoming")] == [factory.booking_code(soon)]
    assert len(reservations(status="past")) == 1 and len(reservations(status="cancelled")) == 1
    first = reservations(status="upcoming")[0]
    assert (first["guest_last_initial"], first["nights"], first["payout"]) == ("U", 2, 11500)
    assert "email" not in first

    stats = client.get(f"{API}/stats", headers=host["headers"]).json()
    assert stats == {
        "active_listings": 1, "upcoming_reservations": 1,
        "earnings_this_month": 11500, "earnings_total": 11500,
    }  # fmt: skip
    rival_view = client.get(
        f"{API}/stats", headers={"Authorization": f"Bearer {rival_token}"}
    ).json()
    assert rival_view["upcoming_reservations"] == 1 and rival_view["earnings_total"] == 0
