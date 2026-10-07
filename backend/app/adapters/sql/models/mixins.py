from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.sql.types import UTCDateTime


def string_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """A VARCHAR column holding the enum's values, guarded by a named CHECK constraint."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [m.value for m in members],
    )


def now_column() -> Mapped[datetime]:
    return mapped_column(UTCDateTime, server_default=func.current_timestamp())
