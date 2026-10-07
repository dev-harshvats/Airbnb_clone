"""Uniform error contract: every error response is {"detail": str, "code": str}."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import DomainError, ErrorKind

_KIND_STATUS = {
    ErrorKind.BAD_REQUEST: 400,
    ErrorKind.UNPROCESSABLE: 422,
    ErrorKind.UNAUTHENTICATED: 401,
    ErrorKind.FORBIDDEN: 403,
    ErrorKind.NOT_FOUND: 404,
    ErrorKind.CONFLICT: 409,
}

_HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    429: "RATE_LIMITED",
}


class AppError(Exception):
    """A business or request error with a stable, machine-readable code."""

    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail


def error_response(status: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail, "code": code})


def _format_validation_error(exc: RequestValidationError) -> str:
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    return f"{location}: {first.get('msg', 'Invalid input')}"


async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status, exc.code, exc.detail)


async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    return error_response(_KIND_STATUS[exc.kind], exc.code, exc.detail)


async def _handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
    return error_response(exc.status_code, code, str(exc.detail))


async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(422, "VALIDATION_ERROR", _format_validation_error(exc))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
