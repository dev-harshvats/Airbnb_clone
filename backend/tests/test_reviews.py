from datetime import timedelta

import pytest

API = "/api/v1"
REVIEW = {
    "cleanliness": 5, "accuracy": 4, "check_in": 5, "communication": 5,
    "location": 4, "value": 5, "comment": "Wonderful stay, would return.",
}  # fmt: skip


@pytest.fixture
def stay(factory, make_user, clock):
    host, _ = make_user(is_host=True)
    guest, guest_token = make_user()
    listing = factory.listing(host.id, factory.category())
    today = clock.today()
    done = factory.booking(listing, guest.id, today - timedelta(days=10), today - timedelta(days=7))
    ahead = factory.booking(
        listing, guest.id, today + timedelta(days=10), today + timedelta(days=12)
    )
    return {
        "host": host, "guest": guest, "listing": listing, "done": factory.booking_code(done),
        "ahead": factory.booking_code(ahead), "headers": {"Authorization": f"Bearer {guest_token}"},
    }  # fmt: skip


def review(client, stay, code=None, **overrides):
    return client.post(
        f"{API}/bookings/{code or stay['done']}/review",
        json=REVIEW | overrides,
        headers=stay["headers"],
    )


def test_a_stay_can_only_be_reviewed_after_checkout(client, stay):
    res = review(client, stay, code=stay["ahead"])
    assert (res.status_code, res.json()["code"]) == (400, "STAY_NOT_COMPLETED")
    trips = client.get(f"{API}/bookings?scope=past", headers=stay["headers"]).json()
    assert [(t["code"], t["can_review"]) for t in trips] == [(stay["done"], True)]


def test_a_review_updates_the_listing_and_can_only_be_left_once(client, stay):
    assert review(client, stay).status_code == 201
    again = review(client, stay)
    assert (again.status_code, again.json()["code"]) == (409, "REVIEW_EXISTS")

    detail = client.get(f"{API}/listings/{stay['listing']}").json()
    assert (detail["review_count"], detail["rating_avg"]) == (
        1,
        5,
    )  # overall = rounded average of 4.67
    assert detail["rating_breakdown"]["accuracy"] == 4
    assert detail["rating_distribution"]["5"] == 1

    page = client.get(f"{API}/listings/{stay['listing']}/reviews").json()
    assert page["total"] == 1
    assert page["items"][0]["comment"] == REVIEW["comment"]
    assert page["items"][0]["author_last_initial"] == "U"  # no full surname, no email

    trips = client.get(f"{API}/bookings?scope=past", headers=stay["headers"]).json()
    assert (trips[0]["has_review"], trips[0]["can_review"]) == (True, False)


def test_only_the_guest_who_stayed_can_review(client, stay, make_user):
    _, other_token = make_user()
    res = client.post(
        f"{API}/bookings/{stay['done']}/review",
        json=REVIEW,
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 404
    assert review(client, stay, cleanliness=6).status_code == 422  # stars are 1-5


def test_a_host_becomes_a_superhost_after_ten_five_star_stays(client, stay, factory, clock):
    today = clock.today()
    for i in range(9):  # nine reviewed stays already on record
        start = today - timedelta(days=100 + i * 5)
        booking = factory.booking(
            stay["listing"], stay["guest"].id, start, start + timedelta(days=2)
        )
        factory.review(booking, stay["listing"], stay["guest"].id, rating=5)
    host = f"{API}/users/{stay['host'].id}"
    assert client.get(host).json()["is_superhost"] is False

    assert (
        review(client, stay, **{k: 5 for k in REVIEW if k != "comment"}).status_code == 201
    )  # the 10th
    assert client.get(host).json()["is_superhost"] is True
