from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


def _safe_image_url(value: str | None) -> str | None:
    """Only same-site media paths or https URLs: never `javascript:` or `data:` URLs."""
    if value is None or value.startswith(("/media/", "https://")):
        return value
    raise ValueError("avatar_url must be a /media/ path or an https:// URL")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    avatar_url: str | None
    is_host: bool
    is_superhost: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Profile fields a user may change. Anything else (email, is_host, ...) is rejected."""

    model_config = ConfigDict(extra="forbid")

    first_name: Name | None = None
    last_name: Name | None = None
    bio: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    avatar_url: Annotated[str | None, AfterValidator(_safe_image_url), Field(max_length=500)] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value


class HostProfileOut(BaseModel):
    """What the world may see about a host: no email, no birth date, only a last initial."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    avatar_url: str | None
    bio: str | None
    is_superhost: bool
    joined_at: datetime = Field(validation_alias="created_at")

    last_name: str = Field(exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_initial(self) -> str:
        return self.last_name[:1]
