"""Application settings, loaded from environment variables (twelve-factor)."""

from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from limits import parse_many
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-only-insecure-jwt-secret-never-use-in-production"
_INSECURE_SECRET_ALLOWED = {"development", "test"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./data/airbnb.db"
    MEDIA_DIR: Path = Path("media")
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    JWT_SECRET: str = DEFAULT_JWT_SECRET
    ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 7
    COOKIE_SECURE: bool = False
    BCRYPT_ROUNDS: int = 12

    # Trust X-Forwarded-For for the client IP. Enable only when every request really arrives
    # through a proxy you control (the Next.js rewrite or Nginx), never when exposed directly.
    TRUST_PROXY_HEADERS: bool = False

    # Rate limits, "<count>/<unit>" (see the `limits` library). Credential endpoints are limited
    # per client IP; the default matches the SRS (5 attempts per minute).
    AUTH_RATE_LIMIT: str = "5/minute"
    LOOKUP_RATE_LIMIT: str = "20/minute"

    SERVICE_FEE_RATE: float = 0.14
    TAX_RATE: float = 0.12

    @property
    def access_ttl(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TTL_MIN)

    @property
    def refresh_ttl(self) -> timedelta:
        return timedelta(days=self.REFRESH_TTL_DAYS)

    @field_validator("AUTH_RATE_LIMIT", "LOOKUP_RATE_LIMIT")
    @classmethod
    def _valid_rate_limit(cls, value: str) -> str:
        try:
            parse_many(value)
        except ValueError as exc:
            raise ValueError(
                f"not a valid rate limit: {value!r} (expected e.g. '5/minute')"
            ) from exc
        return value

    @model_validator(mode="after")
    def _require_real_secret_outside_development(self) -> "Settings":
        if self.ENV not in _INSECURE_SECRET_ALLOWED and self.JWT_SECRET == DEFAULT_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set to a strong secret outside development")
        if self.ENV not in _INSECURE_SECRET_ALLOWED and len(self.JWT_SECRET) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
