import pytest

API = "/api/v1/wishlists"


@pytest.fixture
def setup(factory, make_user):
    host, _ = make_user(is_host=True)
    user, token = make_user()
    _, other_token = make_user()
    category = factory.category()
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "other": {"Authorization": f"Bearer {other_token}"},
        "goa": factory.listing(host.id, category, title="Goa villa"),
        "manali": factory.listing(host.id, category, title="Manali cottage", city="Manali"),
    }


def test_save_list_and_remove_listings(client, setup):
    headers = setup["headers"]
    created = client.post(API, json={"name": "Summer trip"}, headers=headers)
    assert created.status_code == 201
    wishlist = created.json()
    assert (wishlist["name"], wishlist["item_count"], wishlist["cover_url"]) == (
        "Summer trip",
        0,
        None,
    )

    for key in ("goa", "manali", "goa"):  # saving twice changes nothing
        assert (
            client.put(f"{API}/{wishlist['id']}/items/{setup[key]}", headers=headers).status_code
            == 204
        )

    mine = client.get(API, headers=headers).json()
    assert [(w["name"], w["item_count"]) for w in mine] == [("Summer trip", 2)]
    assert mine[0]["cover_url"].endswith("_card.webp")  # first saved listing's photo

    assert set(client.get(f"{API}/saved-ids", headers=headers).json()["listing_ids"]) == {
        setup["goa"], setup["manali"],
    }  # fmt: skip
    detail = client.get(f"{API}/{wishlist['id']}", headers=headers).json()
    assert [card["title"] for card in detail["listings"]] == ["Goa villa", "Manali cottage"]

    client.delete(f"{API}/{wishlist['id']}/items/{setup['goa']}", headers=headers)
    assert client.get(f"{API}/saved-ids", headers=headers).json()["listing_ids"] == [
        setup["manali"]
    ]
    assert client.delete(f"{API}/{wishlist['id']}", headers=headers).status_code == 204
    assert client.get(API, headers=headers).json() == []


def test_wishlist_rules(client, setup):
    headers = setup["headers"]
    client.post(API, json={"name": "Trip"}, headers=headers)
    dupe = client.post(API, json={"name": "Trip"}, headers=headers)
    assert (dupe.status_code, dupe.json()["code"]) == (409, "WISHLIST_EXISTS")
    assert (
        client.post(API, json={"name": "Trip"}, headers=setup["other"]).status_code == 201
    )  # per user

    wishlist_id = client.get(API, headers=headers).json()[0]["id"]
    unknown = client.put(f"{API}/{wishlist_id}/items/99999", headers=headers)
    assert (unknown.status_code, unknown.json()["code"]) == (404, "LISTING_NOT_FOUND")
    assert client.get(API).status_code == 401


def test_other_peoples_wishlists_are_invisible(client, setup):
    wishlist_id = client.post(API, json={"name": "Private"}, headers=setup["headers"]).json()["id"]
    other = setup["other"]
    for res in (
        client.get(f"{API}/{wishlist_id}", headers=other),
        client.delete(f"{API}/{wishlist_id}", headers=other),
        client.put(f"{API}/{wishlist_id}/items/{setup['goa']}", headers=other),
    ):
        assert (res.status_code, res.json()["code"]) == (404, "WISHLIST_NOT_FOUND")
    assert client.get(API, headers=other).json() == []
