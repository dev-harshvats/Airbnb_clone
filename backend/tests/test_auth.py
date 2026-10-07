import base64
import json
from datetime import date, timedelta

import jwt
import pytest

SIGNUP = {
    "email": "harsh@example.com",
    "password": "Password123",
    "first_name": "Harsh",
    "last_name": "Vats",
    "date_of_birth": "1995-05-17",
}
API = "/api/v1/auth"
COOKIE = "refresh_token"


def signup(client, **overrides):
    return client.post(f"{API}/signup", json=SIGNUP | overrides)


def login(client, email="harsh@example.com", password="Password123"):
    return client.post(f"{API}/login", json={"email": email, "password": password})


def set_cookie(client, token):
    client.cookies.clear()
    client.cookies.set(COOKIE, token, domain="testserver.local", path="/api/v1/auth")


def refresh_with(client, token, **headers):
    """Call /auth/refresh presenting exactly this refresh cookie."""
    client.cookies.clear()
    if token is not None:
        set_cookie(client, token)
    return client.post(f"{API}/refresh", headers=headers)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- sign up ----------


def test_signup_returns_token_and_sets_cookie(client):
    res = signup(client)
    assert res.status_code == 201
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    assert body["user"]["email"] == "harsh@example.com"
    assert body["user"]["is_host"] is False
    assert "password" not in json.dumps(body)

    cookie = res.headers["set-cookie"].lower()
    assert f"{COOKIE}=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/api/v1/auth" in cookie
    assert f"max-age={7 * 24 * 3600}" in cookie

    me = client.get(f"{API}/me", headers=bearer(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["id"] == body["user"]["id"]


def test_signup_normalizes_email(client):
    res = signup(client, email="  Harsh@Example.COM ")
    assert res.json()["user"]["email"] == "harsh@example.com"


@pytest.mark.parametrize(
    "password",
    [
        "short1",  # too short
        "onlyletters",  # no digit
        "12345678",  # no letter
        "a1" + "x" * 71,  # 73 bytes
    ],
)
def test_signup_rejects_weak_password(client, password):
    res = signup(client, password=password)
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_signup_accepts_72_byte_password(client):
    assert signup(client, password="a1" + "x" * 70).status_code == 201


def test_signup_rejects_multibyte_password_over_72_bytes(client):
    # 41 characters but 81 bytes in UTF-8
    assert signup(client, password="1" + "é" * 40).status_code == 422


def test_signup_rejects_under_18(client):
    res = signup(client, date_of_birth="2010-01-01")
    assert res.status_code == 422
    assert res.json()["code"] == "UNDER_AGE"


def test_signup_age_boundary_is_the_18th_birthday(client, clock):
    today = clock.today()
    eighteen_today = date(today.year - 18, today.month, today.day)
    tomorrow_birthday = eighteen_today + timedelta(days=1)

    ok = signup(client, email="a@example.com", date_of_birth=eighteen_today.isoformat())
    assert ok.status_code == 201
    res = signup(client, email="b@example.com", date_of_birth=tomorrow_birthday.isoformat())
    assert res.status_code == 422 and res.json()["code"] == "UNDER_AGE"


def test_signup_rejects_impossible_birth_dates(client):
    assert signup(client, date_of_birth="1850-01-01").status_code == 422
    assert signup(client, date_of_birth="2999-01-01").status_code == 422


def test_signup_rejects_blank_names_and_bad_email(client):
    assert signup(client, first_name="   ").status_code == 422
    assert signup(client, email="not-an-email").status_code == 422


def test_duplicate_email_409(client):
    assert signup(client).status_code == 201
    res = signup(client, email="HARSH@example.com")
    assert res.status_code == 409
    assert res.json()["code"] == "EMAIL_TAKEN"


# ---------- check email ----------


def test_check_email_reports_existence_case_insensitively(client):
    signup(client)
    yes = client.post(f"{API}/check-email", json={"email": "Harsh@Example.com"})
    no = client.post(f"{API}/check-email", json={"email": "nobody@example.com"})
    assert yes.json() == {"exists": True}
    assert no.json() == {"exists": False}


# ---------- login ----------


def test_login_success_sets_cookie(client):
    signup(client)
    client.cookies.clear()
    res = login(client)
    assert res.status_code == 200
    assert res.json()["access_token"]
    assert COOKIE in res.cookies


def test_login_wrong_password_401(client):
    signup(client)
    client.cookies.clear()
    res = login(client, password="WrongPassword1")
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_CREDENTIALS"
    assert COOKIE not in res.cookies


def test_login_unknown_email_is_indistinguishable_from_wrong_password(client):
    signup(client)
    wrong = login(client, password="WrongPassword1")
    unknown = login(client, email="ghost@example.com")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_login_with_overlong_password_is_401_not_500(client):
    signup(client)
    res = login(client, password="x" * 120)
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_CREDENTIALS"


def test_login_is_rate_limited_after_five_attempts(client):
    signup(client)
    for _ in range(5):
        assert login(client, password="WrongPassword1").status_code == 401
    res = login(client, password="Password123")
    assert res.status_code == 429
    assert res.json()["code"] == "RATE_LIMITED"


def test_signup_is_rate_limited_after_five_attempts(client):
    for i in range(5):
        assert signup(client, email=f"u{i}@example.com").status_code == 201
    assert signup(client, email="u6@example.com").status_code == 429


def test_rate_limit_ignores_forwarded_header_unless_proxy_is_trusted(client):
    signup(client)
    for _ in range(5):
        login(client, password="WrongPassword1")
    spoofed = client.post(
        f"{API}/login",
        json={"email": "harsh@example.com", "password": "Password123"},
        headers={"X-Forwarded-For": "203.0.113.9"},
    )
    assert spoofed.status_code == 429


def test_rate_limit_is_per_client_ip_when_behind_trusted_proxy(make_client):
    client = make_client(TRUST_PROXY_HEADERS=True)
    signup(client)

    def attempt(real_ip, forged="198.51.100.77"):
        # "<whatever the client claimed>, <the address our proxy saw>"
        return client.post(
            f"{API}/login",
            json={"email": "harsh@example.com", "password": "WrongPassword1"},
            headers={"X-Forwarded-For": f"{forged}, {real_ip}"},
        )

    for i in range(5):
        assert attempt("203.0.113.1", forged=f"198.51.100.{i}").status_code == 401
    # Rotating the forged part does not buy a fresh allowance...
    assert attempt("203.0.113.1", forged="198.51.100.200").status_code == 429
    # ...while a genuinely different visitor is unaffected.
    assert attempt("203.0.113.2").status_code == 401


def test_rate_limit_comes_from_settings(make_client):
    client = make_client(AUTH_RATE_LIMIT="2/minute")
    signup(client)
    assert login(client, password="WrongPassword1").status_code == 401
    assert login(client, password="WrongPassword1").status_code == 401
    assert login(client, password="WrongPassword1").status_code == 429


# ---------- access tokens ----------


def test_me_requires_token(client):
    res = client.get(f"{API}/me")
    assert res.status_code == 401
    assert res.json()["code"] == "NOT_AUTHENTICATED"


def test_me_rejects_garbage_token(client):
    res = client.get(f"{API}/me", headers=bearer("not.a.jwt"))
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_TOKEN"


def test_expired_access_token_is_rejected(client, clock):
    token = signup(client).json()["access_token"]
    clock.advance(minutes=14)
    assert client.get(f"{API}/me", headers=bearer(token)).status_code == 200
    clock.advance(minutes=2)
    res = client.get(f"{API}/me", headers=bearer(token))
    assert res.status_code == 401 and res.json()["code"] == "INVALID_TOKEN"


def test_token_signed_with_another_secret_is_rejected(client, make_user):
    user, _ = make_user()
    forged = jwt.encode(
        {"sub": str(user.id), "type": "access", "jti": "x", "iat": 1, "exp": 9999999999},
        "an-attacker-secret-an-attacker-secret-1234",
        algorithm="HS256",
    )
    assert client.get(f"{API}/me", headers=bearer(forged)).status_code == 401


def test_unsigned_alg_none_token_is_rejected(client, make_user):
    user, _ = make_user()

    def b64(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()

    header = b64({"alg": "none", "typ": "JWT"})
    claims = b64({"sub": str(user.id), "type": "access", "jti": "x", "iat": 1, "exp": 9999999999})
    forged = f"{header}.{claims}."
    assert client.get(f"{API}/me", headers=bearer(forged)).status_code == 401


def test_refresh_token_cannot_be_used_as_access_token(client):
    res = signup(client)
    out = client.get(f"{API}/me", headers=bearer(res.cookies[COOKIE]))
    assert out.status_code == 401 and out.json()["code"] == "INVALID_TOKEN"


def test_access_token_cannot_be_used_as_refresh_token(client):
    access = signup(client).json()["access_token"]
    assert refresh_with(client, access).status_code == 401


def test_token_of_deleted_user_is_rejected(client, app, make_user):
    from sqlalchemy import text

    user, token = make_user()
    with app.state.engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})
    assert client.get(f"{API}/me", headers=bearer(token)).status_code == 401


# ---------- refresh rotation ----------


def test_refresh_rotates_token(client):
    first = signup(client)
    old_cookie = first.cookies[COOKIE]

    second = refresh_with(client, old_cookie)
    assert second.status_code == 200
    new_cookie = second.cookies[COOKIE]
    assert new_cookie != old_cookie
    assert second.json()["access_token"]
    assert second.json()["user"]["email"] == "harsh@example.com"

    replay = refresh_with(client, old_cookie)  # the old cookie can't be reused
    assert replay.status_code == 401
    assert replay.json()["code"] == "INVALID_TOKEN"


def test_refresh_reuse_revokes_family(client):
    old_cookie = signup(client).cookies[COOKIE]
    newest_cookie = refresh_with(client, old_cookie).cookies[COOKIE]

    assert refresh_with(client, old_cookie).status_code == 401  # replay detected
    assert refresh_with(client, newest_cookie).status_code == 401  # whole family is dead


def test_reuse_detection_does_not_touch_other_sessions(client):
    signup(client)
    phone = login(client).cookies[COOKIE]
    laptop = login(client).cookies[COOKIE]
    laptop_next = refresh_with(client, laptop).cookies[COOKIE]
    refresh_with(client, laptop)  # replay -> laptop family revoked

    assert refresh_with(client, laptop_next).status_code == 401
    assert refresh_with(client, phone).status_code == 200


def test_expired_refresh_token_is_rejected(client, clock):
    cookie = signup(client).cookies[COOKIE]
    clock.advance(days=7, minutes=1)
    assert refresh_with(client, cookie).status_code == 401


def test_refresh_without_cookie_401(client):
    res = refresh_with(client, None)
    assert res.status_code == 401
    assert res.json()["code"] == "MISSING_REFRESH_TOKEN"


def test_refresh_rejects_foreign_origin(client):
    cookie = signup(client).cookies[COOKIE]
    res = refresh_with(client, cookie, Origin="https://evil.test")
    assert res.status_code == 403
    assert res.json()["code"] == "BAD_ORIGIN"
    # the rejected request must not have burned the token
    assert refresh_with(client, cookie, Origin="http://localhost:3000").status_code == 200


def test_refresh_allows_missing_origin(client):
    cookie = signup(client).cookies[COOKIE]
    assert refresh_with(client, cookie).status_code == 200


# ---------- logout ----------


def test_logout_revokes(client):
    cookie = signup(client).cookies[COOKIE]
    set_cookie(client, cookie)
    res = client.post(f"{API}/logout")
    assert res.status_code == 204
    assert "max-age=0" in res.headers["set-cookie"].lower()
    assert refresh_with(client, cookie).status_code == 401


def test_logout_without_cookie_is_a_no_op(client):
    assert client.post(f"{API}/logout").status_code == 204


def test_logout_rejects_foreign_origin(client):
    cookie = signup(client).cookies[COOKIE]
    set_cookie(client, cookie)
    res = client.post(f"{API}/logout", headers={"Origin": "https://evil.test"})
    assert res.status_code == 403
    assert refresh_with(client, cookie).status_code == 200  # still valid
