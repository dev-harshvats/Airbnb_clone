from datetime import date

import pytest

API = "/api/v1"
NOV = date(2026, 11, 1)


@pytest.fixture
def catalog(factory, make_user):
    """Three Goa/Manali listings, one unpublished, and the people around them."""
    host, host_token = make_user(is_host=True)
    guest, guest_token = make_user()
    category = factory.category()
    wifi, pool, ac = factory.amenity("wifi"), factory.amenity("pool"), factory.amenity("ac")
    ids = {
        "cheap": factory.listing(
            host.id, category, [wifi, pool], price_per_night=3000, max_guests=2
        ),
        "big": factory.listing(
            host.id, category, [wifi], price_per_night=8000, max_guests=6, pets_allowed=True
        ),
        "manali": factory.listing(
            host.id, category, [wifi, ac], city="Manali", state="Himachal Pradesh",
            price_per_night=5000, max_guests=4,
        ),
        "draft": factory.listing(host.id, category, status="inactive", price_per_night=4000),
    }  # fmt: skip
    return {"host": host, "host_token": host_token, "guest": guest, "guest_token": guest_token,
            "ids": ids}  # fmt: skip


def search(client, **params):
    res = client.get(f"{API}/listings", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def titles_ids(page):
    return {item["id"] for item in page["items"]}


def test_filter_by_location_price_and_guests(client, catalog):
    ids = catalog["ids"]
    goa = search(client, location="goa")
    assert titles_ids(goa) == {ids["cheap"], ids["big"]}  # the unpublished listing is hidden

    assert titles_ids(search(client, location="goa", max_price=5000)) == {ids["cheap"]}
    assert titles_ids(search(client, adults=4)) == {ids["big"], ids["manali"]}
    assert titles_ids(search(client, adults=2, pets=1)) == {ids["big"]}  # only it allows pets
    assert titles_ids(search(client, place_type="private_room")) == set()


def test_confirmed_bookings_hide_a_listing_for_those_dates_only(client, catalog, factory):
    ids, guest = catalog["ids"], catalog["guest"]
    factory.booking(ids["cheap"], guest.id, date(2026, 11, 10), date(2026, 11, 13))
    factory.booking(
        ids["big"], guest.id, date(2026, 11, 10), date(2026, 11, 13), status="cancelled"
    )

    dates = {"check_in": "2026-11-11", "check_out": "2026-11-12", "location": "goa"}
    assert titles_ids(search(client, **dates)) == {ids["big"]}  # cancelled stay doesn't block
    back_to_back = {"check_in": "2026-11-13", "check_out": "2026-11-15", "location": "goa"}
    assert titles_ids(search(client, **back_to_back)) == {ids["cheap"], ids["big"]}


def test_searching_with_dates_shows_the_total_for_those_dates(client, catalog):
    page = search(client, check_in="2026-11-10", check_out="2026-11-13", location="manali")
    assert page["items"][0]["total_for_dates"] == 20580  # 3 nights, fees and taxes included
    assert search(client, location="manali")["items"][0]["total_for_dates"] is None


def test_amenity_filter_requires_all_of_them(client, catalog):
    ids = catalog["ids"]
    assert titles_ids(search(client, amenities=["wifi"])) == {
        ids["cheap"],
        ids["big"],
        ids["manali"],
    }
    assert titles_ids(search(client, amenities=["wifi", "pool"])) == {ids["cheap"]}
    assert titles_ids(search(client, amenities=["pool", "ac"])) == set()


def test_pagination_and_sorting(client, catalog):
    ids = catalog["ids"]
    first = search(client, page_size=2, sort="price_asc")
    assert (first["total"], first["page"], len(first["items"])) == (3, 1, 2)
    assert [i["id"] for i in first["items"]] == [ids["cheap"], ids["manali"]]
    second = search(client, page=2, page_size=2, sort="price_asc")
    assert [i["id"] for i in second["items"]] == [ids["big"]]
    assert client.get(f"{API}/listings", params={"page_size": 500}).status_code == 422


def test_price_histogram_has_20_buckets_covering_every_match(client, catalog):
    body = client.get(f"{API}/listings/price-histogram", params={"max_price": 4000}).json()
    # the price filter itself is ignored so the slider keeps showing the whole range
    assert (body["min_price"], body["max_price"]) == (3000, 8000)
    assert len(body["buckets"]) == 20 and sum(body["buckets"]) == 3


def test_listing_detail_shows_the_address_only_to_the_host(client, catalog, auth):
    listing_id = catalog["ids"]["cheap"]
    public = client.get(f"{API}/listings/{listing_id}").json()
    assert public["host"]["id"] == catalog["host"].id and "email" not in public["host"]
    assert [a["key"] for a in public["amenities"]] == ["wifi", "pool"]
    assert len(public["all_photos"]) == 5 and len(public["photos"]) == 5
    assert public["address_line"] is None
    assert public["rating_distribution"] == {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}

    mine = client.get(f"{API}/listings/{listing_id}", headers=auth(catalog["host_token"])).json()
    assert mine["address_line"] == "12 Beach Road"


def test_unpublished_listings_are_only_visible_to_their_host(client, catalog, auth):
    draft = catalog["ids"]["draft"]
    assert client.get(f"{API}/listings/{draft}").status_code == 404
    assert (
        client.get(f"{API}/listings/{draft}", headers=auth(catalog["guest_token"])).status_code
        == 404
    )
    assert (
        client.get(f"{API}/listings/{draft}", headers=auth(catalog["host_token"])).status_code
        == 200
    )
    assert client.get(f"{API}/listings/999999").status_code == 404


def test_availability_and_quote(client, catalog, factory):
    ids, guest = catalog["ids"], catalog["guest"]
    factory.booking(ids["cheap"], guest.id, date(2026, 11, 10), date(2026, 11, 13))
    free = client.get(f"{API}/listings/{ids['cheap']}/availability", params={"from": "2026-11-01"})
    assert free.json() == {"booked": [{"check_in": "2026-11-10", "check_out": "2026-11-13"}]}

    body = {"check_in": "2026-11-20", "check_out": "2026-11-23"}
    ok = client.post(f"{API}/listings/{ids['cheap']}/quote", json=body)
    assert ok.json() == {
        "nightly_rate": 3000, "nights": 3, "subtotal": 9000, "cleaning_fee": 1500,
        "service_fee": 1260, "taxes": 1260, "total": 13020,
    }  # fmt: skip
    taken = {"check_in": "2026-11-11", "check_out": "2026-11-12"}
    res = client.post(f"{API}/listings/{ids['cheap']}/quote", json=taken)
    assert (res.status_code, res.json()["code"]) == (409, "BOOKING_CONFLICT")


def test_reference_data_and_location_suggestions(client, catalog):
    categories = client.get(f"{API}/categories")
    assert [c["slug"] for c in categories.json()] == ["beachfront"]
    assert categories.headers["cache-control"] == "public, max-age=3600"
    amenities = client.get(f"{API}/amenities")
    assert {a["key"] for a in amenities.json()} == {"wifi", "pool", "ac"}
    suggested = client.get(f"{API}/locations/suggest", params={"q": "man"}).json()
    assert suggested == [
        {"label": "Manali, Himachal Pradesh", "city": "Manali", "state": "Himachal Pradesh"}
    ]
    assert client.get(f"{API}/locations/suggest", params={"q": ""}).json() == []


def test_destinations_list_cities_with_stays_and_a_cover_photo(client, catalog):
    body = client.get(f"{API}/destinations").json()
    assert (
        body[0]["city"] == "Goa" and body[0]["listing_count"] == 2
    )  # the unlisted stay is not counted
    assert {d["city"] for d in body} == {"Goa", "Manali"}
    assert body[0]["cover_url"].endswith("_card.webp")
