from datetime import date, datetime, timedelta

from app.domain.timezones import IST


class FixedClock:
    """A Clock whose time only moves when a test says so."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def today(self) -> date:
        return self._now.astimezone(IST).date()

    def advance(self, **delta) -> None:
        self._now += timedelta(**delta)
