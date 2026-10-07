import json
import logging

import pytest

from app.core.config import Settings


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ready(client):
    res = client.get("/api/v1/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready", "database": "ok"}


def test_request_id_header_is_echoed(client):
    res = client.get("/api/v1/health", headers={"X-Request-ID": "abc-123"})
    assert res.headers["X-Request-ID"] == "abc-123"


def test_request_id_header_is_generated(client):
    res = client.get("/api/v1/health")
    assert len(res.headers["X-Request-ID"]) >= 16


def test_unknown_route_uses_error_shape(client):
    res = client.get("/api/v1/does-not-exist")
    assert res.status_code == 404
    assert res.json() == {"detail": "Not Found", "code": "NOT_FOUND"}


def test_access_log_is_json_with_request_id(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/api/v1/health", headers={"X-Request-ID": "log-1"})
    record = json.loads(caplog.records[-1].getMessage())
    assert record["request_id"] == "log-1"
    assert record["path"] == "/api/v1/health"
    assert record["status"] == 200
    assert "duration_ms" in record


def test_default_jwt_secret_rejected_outside_development():
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(ENV="production")


def test_default_jwt_secret_allowed_in_development():
    assert Settings(ENV="development").JWT_SECRET


def _client_with_route(settings, handler):
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(settings)
    app.add_api_route("/api/v1/_boom", handler)
    return TestClient(app, raise_server_exceptions=False)


def test_app_error_uses_error_shape(settings):
    from app.core.errors import AppError

    def boom():
        raise AppError(409, "BOOKING_CONFLICT", "Those dates are no longer available.")

    res = _client_with_route(settings, boom).get("/api/v1/_boom")
    assert res.status_code == 409
    assert res.json() == {
        "detail": "Those dates are no longer available.",
        "code": "BOOKING_CONFLICT",
    }


def test_unhandled_exception_returns_internal_without_leaking(settings):
    def boom():
        raise RuntimeError("secret stack detail")

    res = _client_with_route(settings, boom).get("/api/v1/_boom")
    assert res.status_code == 500
    assert res.json()["code"] == "INTERNAL"
    assert "secret" not in res.text
    assert res.headers["X-Request-ID"]


def test_validation_error_uses_error_shape(settings):
    def needs_int(n: int):
        return {"n": n}

    res = _client_with_route(settings, needs_int).get("/api/v1/_boom?n=abc")
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_sqlite_pragmas_enabled(client):
    from sqlalchemy import text

    engine = client.app.state.engine
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == 5000
