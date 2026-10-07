import pytest
from fastapi.testclient import TestClient

from app.core.container import HostUser


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_become_host(client, make_user):
    _, token = make_user()
    res = client.post("/api/v1/users/me/become-host", headers=bearer(token))
    assert res.status_code == 200
    assert res.json()["is_host"] is True
    again = client.post("/api/v1/users/me/become-host", headers=bearer(token))
    assert again.status_code == 200 and again.json()["is_host"] is True  # idempotent


def test_become_host_requires_login(client):
    assert client.post("/api/v1/users/me/become-host").status_code == 401


def test_require_host_dependency(app, make_user):
    def host_only(user: HostUser):
        return {"id": user.id}

    app.add_api_route("/api/v1/_host-only", host_only)
    _, guest_token = make_user()
    host, host_token = make_user(is_host=True)
    with TestClient(app) as client:
        denied = client.get("/api/v1/_host-only", headers=bearer(guest_token))
        assert denied.status_code == 403 and denied.json()["code"] == "NOT_HOST"
        ok = client.get("/api/v1/_host-only", headers=bearer(host_token))
        assert ok.json() == {"id": host.id}
        assert client.get("/api/v1/_host-only").status_code == 401


def test_update_profile(client, make_user):
    user, token = make_user()
    res = client.patch(
        "/api/v1/users/me",
        headers=bearer(token),
        json={
            "first_name": "Aarav",
            "bio": "Love the hills",
            "avatar_url": "/media/seed/avatars/1.webp",
        },
    )
    assert res.status_code == 200
    assert res.json()["first_name"] == "Aarav"
    assert res.json()["avatar_url"] == "/media/seed/avatars/1.webp"
    assert res.json()["last_name"] == user.last_name  # untouched fields stay


@pytest.mark.parametrize(
    "payload",
    [
        {"first_name": "  "},
        {"avatar_url": "javascript:alert(1)"},
        {"bio": "x" * 501},
        {"is_host": True},  # privileged fields cannot be set through the profile
        {"email": "other@example.com"},
    ],
)
def test_update_profile_rejects_bad_input(client, make_user, payload):
    _, token = make_user()
    res = client.patch("/api/v1/users/me", headers=bearer(token), json=payload)
    assert res.status_code == 422


def test_public_host_profile_hides_private_data(client, make_user):
    host, _ = make_user(is_host=True, is_superhost=True, bio="Welcome!")
    res = client.get(f"/api/v1/users/{host.id}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == host.id
    assert body["is_superhost"] is True
    assert body["last_initial"] == host.last_name[0]
    for private in ("email", "date_of_birth", "password_hash", "last_name"):
        assert private not in body


def test_non_host_has_no_public_profile(client, make_user):
    guest, _ = make_user()
    assert client.get(f"/api/v1/users/{guest.id}").status_code == 404
    assert client.get("/api/v1/users/99999").status_code == 404
