"""Application settings, loaded from environment variables (twelve-factor)."""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-insecure-secret-change-me"
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

    SERVICE_FEE_RATE: float = 0.14
    TAX_RATE: float = 0.12

    @model_validator(mode="after")
    def _require_real_secret_outside_development(self) -> "Settings":
        if self.ENV not in _INSECURE_SECRET_ALLOWED and self.JWT_SECRET == DEFAULT_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set to a strong secret outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
