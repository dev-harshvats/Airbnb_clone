"""Seeds a database with demo data. Idempotent: it does nothing when users already exist."""

import random
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.adapters.sql.host_reader import SqlHostReader
from app.adapters.sql.models import (
    AmenityModel,
    BookingModel,
    CategoryModel,
    ExperienceModel,
    ExperiencePhotoModel,
    ListingAmenityModel,
    ListingModel,
    ListingPhotoModel,
    RefreshTokenModel,
    ReviewModel,
    ServiceModel,
    ServicePhotoModel,
    UserModel,
    WishlistItemModel,
    WishlistModel,
)
from app.domain.listing_rules import qualifies_as_superhost
from app.seed.builder import (
    create_listings,
    create_reference_data,
    create_users,
    load_photo_pools,
)
from app.seed.catalog import create_experiences, create_services
from app.seed.history import create_history, create_wishlists

RANDOM_SEED = 42

# children before parents, so foreign keys never block the delete
_TABLES = [
    ExperiencePhotoModel, ExperienceModel, ServicePhotoModel, ServiceModel,
    ReviewModel, WishlistItemModel, WishlistModel, BookingModel, ListingAmenityModel,
    ListingPhotoModel, ListingModel, AmenityModel, CategoryModel, RefreshTokenModel, UserModel,
]  # fmt: skip


def reset_database(session: Session) -> None:
    for model in _TABLES:
        session.execute(delete(model))
    session.commit()


def seed_database(
    session: Session,
    media_dir: Path,
    today: date,
    now: datetime,
    reset: bool = False,
    photos_dir: Path | None = None,
) -> bool:
    """Returns True when data was created, False when the database was already seeded.

    Avatars are written under `media_dir`; the bundled photos are read from `photos_dir`
    (which defaults to `media_dir`)."""
    if reset:
        reset_database(session)
    elif session.scalar(select(func.count()).select_from(UserModel)):
        return False

    rng = random.Random(RANDOM_SEED)
    pools = load_photo_pools(photos_dir or media_dir)  # fail early, before writing anything
    category_ids, amenity_ids = create_reference_data(session)
    users = create_users(session, media_dir, now)
    listings = create_listings(session, rng, users, category_ids, amenity_ids, pools, now)
    guests = [u for u in users.values() if not u.is_host]
    create_history(session, rng, listings, guests, today, now)
    create_wishlists(session, rng, guests, [i.id for i in listings if i.id], now)
    create_experiences(session, rng, users, pools, now)
    create_services(session, rng, users, pools, now)
    session.flush()
    _award_superhosts(session, users, today)
    session.commit()
    return True


def _award_superhosts(session: Session, users: dict[str, UserModel], today: date) -> None:
    """Apply the real Superhost rule to the generated history rather than hard-coding badges."""
    reader = SqlHostReader(session)
    for user in users.values():
        if user.is_host:
            user.is_superhost = qualifies_as_superhost(reader.superhost_inputs(user.id, today))
