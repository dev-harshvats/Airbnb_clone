from datetime import UTC, date, datetime

from app.domain.timezones import IST


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def today(self) -> date:
        return self.now().astimezone(IST).date()
