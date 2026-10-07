"""Structured JSON logging and request-ID correlation (SYSTEM_DESIGN §9)."""

import json
import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.errors import error_response

REQUEST_ID_HEADER = "X-Request-ID"
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

access_logger = logging.getLogger("app.access")
error_logger = logging.getLogger("app.errors")


def log_event(logger: logging.Logger, level: int, event: str, **fields) -> None:
    """Emit one JSON log line tagged with the current request id."""
    payload = {"event": event, "request_id": request_id_var.get(), **fields}
    logger.log(level, json.dumps(payload, default=str))


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Request-ID, logs each request, and turns crashes into 500s."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            error_logger.exception("unhandled error (request_id=%s)", request_id)
            response = error_response(500, "INTERNAL", "Something went wrong. Please try again.")
        finally:
            request_id_var.reset(token)

        response.headers[REQUEST_ID_HEADER] = request_id
        access_logger.info(
            json.dumps(
                {
                    "event": "http.request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            )
        )
        return response


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(message)s")
