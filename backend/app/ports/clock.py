from datetime import date, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """The current instant, timezone-aware (UTC)."""

    def today(self) -> date:
        """The current calendar date in the business time zone (India)."""
