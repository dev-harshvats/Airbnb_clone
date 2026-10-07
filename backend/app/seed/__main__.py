"""python -m app.seed [--reset]

Fills the database with demo data: Indian destinations, hosts and guests, listings with photos,
bookings, reviews and wishlists. Safe to run repeatedly; it does nothing once data exists.
"""

import sys

from sqlalchemy import inspect

from app.adapters.clock import SystemClock
from app.core.config import get_settings
from app.core.database import build_engine, build_session_factory
from app.seed.people import DEMO_PASSWORD
from app.seed.runner import seed_database


def main() -> int:
    settings = get_settings()
    engine = build_engine(settings.DATABASE_URL)
    if not inspect(engine).has_table("users"):
        print("The database has no tables yet. Run first: python -m alembic upgrade head")
        return 1
    clock = SystemClock()
    with build_session_factory(engine)() as session:
        created = seed_database(
            session, settings.MEDIA_DIR, clock.today(), clock.now(), reset="--reset" in sys.argv
        )
    if created:
        print(
            f"Seeded demo data. Log in as host@example.com or guest@example.com ({DEMO_PASSWORD})."
        )
    else:
        print("Database already has data; nothing to do (use --reset to start over).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
