"""Business errors, independent of HTTP.

Services raise `DomainError(kind, code, detail)`. The API layer maps `kind` to a status
code (see core/errors.py), so business code never knows about HTTP.
"""

from enum import StrEnum


class ErrorKind(StrEnum):
    BAD_REQUEST = "bad_request"  # a business rule was violated
    UNPROCESSABLE = "unprocessable"  # well-formed input that is not acceptable
    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"


class DomainError(Exception):
    def __init__(self, kind: ErrorKind, code: str, detail: str) -> None:
        super().__init__(detail)
        self.kind = kind
        self.code = code
        self.detail = detail
