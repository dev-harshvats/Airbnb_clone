"""Business-calendar time zone.

Every listing is in India, which has a single fixed offset and no daylight saving, so a
fixed-offset zone is exact and needs no tz database (which Windows does not ship).
"""

from datetime import timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), "IST")
