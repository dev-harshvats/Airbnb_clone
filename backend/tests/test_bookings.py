from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

API = "/api/v1"


@pytest.fixture
def world(factory, make_user):
    host, host_token = make_user(is_host=True)
    guest, guest_token = make_user()
    other, other_token = make_user()
    listing = factory.listing(host.id, factory.category(), price_per_night=5000, cleaning_fee=1500)
    return {
        "host": host, "host_token": host_token, "guest": guest, "guest_token": guest_token,
        "other": other, "other_token": other_token, "listing": listing,
    }  # fmt: skip


def book(client, token, listing, check_in, check_out, **extra):
    headers = {"Authorization": f"Bearer {token}"} | extra.pop("headers", {})
    body = {
        "listing_id": listing,
        "check_in": check_in,
        "check_out": check_out,
        "adults": 2,
        "payment_method": "card",
    } | extra
    return client.post(f"{API}/bookings", json=body, headers=headers)


def test_booking_prices_on_the_server_and_blocks_those_dates(client, world, auth):
    res = book(client, world["guest_token"], world["listing"], "2026-11-10", "2026-11-13")
    assert res.status_code == 201
    b = res.json()
    assert len(b["code"]) == 10 and b["code"].isalnum() and b["code"].isupper()
    assert (b["nights"], b["subtotal"], b["cleaning_fee"], b["service_fee"], b["taxes"]) == (
        3, 15000, 1500, 2100, 1980,
    )  # fmt: skip
    assert b["total"] == 20580 and b["status"] == "confirmed" and b["can_cancel"] is True
    assert b["listing"]["title"] == "Sea-facing villa" and b["listing"]["host_first_name"] == "Test"

    # the dates are now blocked for everyone
    availability = client.get(f"{API}/listings/{world['listing']}/availability").json()
    assert availability["booked"] == [{"check_in": "2026-11-10", "check_out": "2026-11-13"}]
    clash = book(client, world["other_token"], world["listing"], "2026-11-12", "2026-11-14")
    assert (clash.status_code, clash.json()["code"]) == (409, "BOOKING_CONFLICT")

    # it shows up in My Trips and can be fetched by its code
    trips = client.get(f"{API}/bookings", headers=auth(world["guest_token"])).json()
    assert [t["code"] for t in trips] == [b["code"]]
    one = client.get(f"{API}/bookings/{b['code']}", headers=auth(world["guest_token"]))
    assert one.json()["total"] == 20580


def test_back_to_back_stays_are_allowed_but_one_night_of_overlap_is_not(client, world):
    token, listing = world["guest_token"], world["listing"]
    assert book(client, token, listing, "2026-11-10", "2026-11-13").status_code == 201
    assert (
        book(client, token, listing, "2026-11-13", "2026-11-15").status_code == 201
    )  # starts on check-out day
    assert (
        book(client, token, listing, "2026-11-07", "2026-11-10").status_code == 201
    )  # ends on check-in day
    assert (
        book(client, token, listing, "2026-11-14", "2026-11-16").status_code == 409
    )  # one shared night


def test_cancelling_frees_the_dates(client, world, auth):
    token, listing = world["guest_token"], world["listing"]
    code = book(client, token, listing, "2026-11-10", "2026-11-13").json()["code"]

    cancelled = client.post(f"{API}/bookings/{code}/cancel", headers=auth(token))
    assert cancelled.json()["status"] == "cancelled" and cancelled.json()["can_cancel"] is False
    assert (
        client.post(f"{API}/bookings/{code}/cancel", headers=auth(token)).status_code == 200
    )  # idempotent
    assert (
        book(client, world["other_token"], listing, "2026-11-10", "2026-11-13").status_code == 201
    )
    assert [
        t["code"] for t in client.get(f"{API}/bookings?scope=cancelled", headers=auth(token)).json()
    ] == [code]


@pytest.mark.parametrize(
    ("code", "kwargs", "as_host"),
    [
        ("PAST_DATE", {"check_in": "2026-10-06", "check_out": "2026-10-08"}, False),
        ("TOO_MANY_GUESTS", {"adults": 3, "children": 2}, False),
        ("PETS_NOT_ALLOWED", {"pets": 1}, False),
        ("OWN_LISTING", {}, True),
        ("MIN_NIGHTS", {"check_in": "2026-11-10", "check_out": "2026-11-11"}, False),
    ],
)
def test_booking_rules(client, world, factory, make_user, code, kwargs, as_host):
    host_id = world["host"].id
    listing = factory.listing(host_id, factory.category("rules"), min_nights=2, max_guests=4)
    token = world["host_token"] if as_host else world["guest_token"]
    dates = {"check_in": "2026-11-10", "check_out": "2026-11-13"} | kwargs
    res = book(client, token, listing, dates.pop("check_in"), dates.pop("check_out"), **dates)
    assert (res.status_code, res.json()["code"]) == (400, code)


def test_checkout_must_be_after_checkin(client, world):
    res = book(client, world["guest_token"], world["listing"], "2026-11-10", "2026-11-10")
    assert (res.status_code, res.json()["code"]) == (422, "VALIDATION_ERROR")


def test_retrying_with_the_same_idempotency_key_returns_the_same_booking(client, world, auth):
    key = {"headers": {"Idempotency-Key": "checkout-123"}}
    first = book(client, world["guest_token"], world["listing"], "2026-11-10", "2026-11-13", **key)
    again = book(client, world["guest_token"], world["listing"], "2026-11-10", "2026-11-13", **key)
    assert (first.status_code, again.status_code) == (201, 201)
    assert first.json()["code"] == again.json()["code"]
    trips = client.get(f"{API}/bookings", headers=auth(world["guest_token"])).json()
    assert len(trips) == 1


def test_two_simultaneous_requests_for_the_same_dates_cannot_both_win(app, world):
    barrier = Barrier(2)

    def attempt(token):
        with TestClient(app) as client:
            barrier.wait()
            return book(client, token, world["listing"], "2026-12-01", "2026-12-05").status_code

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(attempt, [world["guest_token"], world["other_token"]]))
    assert sorted(results) == [201, 409]


def test_trip_scopes_and_the_checkout_day_boundary(client, world, factory, clock, auth):
    today, guest, listing = clock.today(), world["guest"], world["listing"]
    past = factory.booking(listing, guest.id, today - timedelta(days=10), today - timedelta(days=7))
    ends_today = factory.booking(listing, guest.id, today - timedelta(days=2), today)
    future = factory.booking(
        listing, guest.id, today + timedelta(days=30), today + timedelta(days=32)
    )
    headers = auth(world["guest_token"])

    def codes(scope):
        return [
            t["code"] for t in client.get(f"{API}/bookings?scope={scope}", headers=headers).json()
        ]

    code = factory.booking_code
    assert codes("upcoming") == [
        code(ends_today),
        code(future),
    ]  # a stay ending today is not over yet
    assert codes("past") == [code(past)]
    trip = client.get(f"{API}/bookings/{code(ends_today)}", headers=headers).json()
    assert trip["can_review"] is False and trip["can_cancel"] is False
    started = client.post(f"{API}/bookings/{code(ends_today)}/cancel", headers=headers)
    assert (started.status_code, started.json()["code"]) == (400, "CANNOT_CANCEL")


def test_bookings_are_private_to_their_guest(client, world, factory, auth):
    code = book(client, world["guest_token"], world["listing"], "2026-11-10", "2026-11-13").json()[
        "code"
    ]
    for method, path in [("get", f"/bookings/{code}"), ("post", f"/bookings/{code}/cancel")]:
        res = getattr(client, method)(f"{API}{path}", headers=auth(world["other_token"]))
        assert (res.status_code, res.json()["code"]) == (404, "BOOKING_NOT_FOUND")
    assert client.post(f"{API}/bookings", json={}).status_code == 401
