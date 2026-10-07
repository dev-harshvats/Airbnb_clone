"""Builds reference data, users and listings (with photos and amenities) for the demo."""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.adapters.security.bcrypt_hasher import BcryptHasher
from app.adapters.sql.models import (
    AmenityModel,
    CategoryModel,
    ListingAmenityModel,
    ListingModel,
    ListingPhotoModel,
    UserModel,
)
from app.seed.avatars import avatar_url_for
from app.seed.content import (
    ADJECTIVES,
    AMENITY_SENTENCES,
    ARCHETYPES,
    CLOSERS,
    HOUSE_RULES,
    Archetype,
)
from app.seed.destinations import DESTINATIONS, Destination
from app.seed.people import DEMO_PASSWORD, PEOPLE
from app.seed.reference import AMENITIES, CATEGORIES

PET_FRIENDLY = {
    "beach_villa", "beach_cottage", "hill_cottage", "cabin_stay",
    "plantation_bungalow", "farm_stay", "colonial_house",
}  # fmt: skip


@dataclass(frozen=True)
class ListingInfo:
    """What the booking history needs to know about a listing."""

    id: int
    host_key: str
    host_id: int
    price: int
    cleaning_fee: int
    min_nights: int
    max_guests: int
    pets_allowed: bool


def create_reference_data(session: Session) -> tuple[dict[str, int], dict[str, int]]:
    categories = {slug: CategoryModel(slug=slug, label=label, icon_key=icon, sort_order=i)
                  for i, (slug, label, icon) in enumerate(CATEGORIES)}  # fmt: skip
    amenities = {key: AmenityModel(key=key, name=name, icon_key=icon, group=group)
                 for key, name, icon, group in AMENITIES}  # fmt: skip
    session.add_all([*categories.values(), *amenities.values()])
    session.flush()
    return {k: v.id for k, v in categories.items()}, {k: v.id for k, v in amenities.items()}


def create_users(session: Session, media_dir: Path, now: datetime) -> dict[str, UserModel]:
    password_hash = BcryptHasher(12).hash(DEMO_PASSWORD)  # one hash is shared by every demo user
    users = {}
    for index, (key, email, first, last, born, is_host, bio) in enumerate(PEOPLE):
        users[key] = UserModel(
            email=email, password_hash=password_hash, first_name=first, last_name=last,
            date_of_birth=born, avatar_url=avatar_url_for(index, first, last, media_dir),
            bio=bio, is_host=is_host, is_superhost=False,
            created_at=now - timedelta(days=700 - index * 40), updated_at=now,
        )  # fmt: skip
    session.add_all(users.values())
    session.flush()
    return users


def load_photo_pools(media_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """theme -> [(full url, card url)], read from the downloaded photo folders."""
    root = Path(media_dir) / "seed" / "photos"
    if not root.is_dir():
        raise SystemExit(
            f"Seed photos not found at {root}. Run: python -m app.seed.photo_tools download"
        )
    pools = {}
    for folder in sorted(root.iterdir()):
        pools[folder.name] = [
            (f"/media/seed/photos/{folder.name}/{p.name}",
             f"/media/seed/photos/{folder.name}/{p.stem}_card.webp")
            for p in sorted(folder.glob("[0-9][0-9].webp"))
        ]  # fmt: skip
    return pools


def pick_photos(
    pools: dict[str, list[tuple[str, str]]], themes: tuple[str, ...], seed: int, count: int = 5
) -> list[tuple[str, str]]:
    """Five distinct photos: two from the main theme, the rest from the supporting themes."""
    chosen: list[tuple[str, str]] = []
    plan = [(0, 0), (0, 3), (1, 0), (2, 1), (1, 2), (0, 6), (2, 3), (1, 5)]  # (theme index, offset)
    for theme_index, offset in plan:
        pool = pools.get(themes[min(theme_index, len(themes) - 1)]) or []
        if not pool:
            continue
        photo = pool[(seed + offset) % len(pool)]
        if photo not in chosen:
            chosen.append(photo)
        if len(chosen) == count:
            break
    return chosen


def _title(rng: random.Random, arch: Archetype, taken: set[str]) -> str:
    for _ in range(50):
        title = f"{rng.choice(ADJECTIVES)} {rng.choice(arch.nouns)}"
        if rng.random() < 0.7:
            title += f" {rng.choice(arch.features)}"
        if title not in taken:
            taken.add(title)
            return title
    return f"{title} {len(taken)}"


def _description(
    rng: random.Random, arch: Archetype, dest: Destination, amenity_keys: list[str]
) -> str:
    sentences = [AMENITY_SENTENCES[k] for k in amenity_keys if k in AMENITY_SENTENCES][:2]
    location = f"It sits {rng.choice(dest.highlights)}, in {dest.city}, {dest.state}."
    return " ".join([arch.opener, location, *sentences, rng.choice(CLOSERS)])


def create_listings(
    session: Session,
    rng: random.Random,
    users: dict[str, UserModel],
    category_ids: dict[str, int],
    amenity_ids: dict[str, int],
    pools: dict[str, list[tuple[str, str]]],
    now: datetime,
) -> list[ListingInfo]:
    infos: list[ListingInfo] = []
    taken_titles: set[str] = set()
    counter = 0
    for dest in DESTINATIONS:
        host = users[dest.host]
        for stay_key in dest.stays:
            arch = ARCHETYPES[stay_key]
            counter += 1
            bedrooms = rng.randint(*arch.bedrooms)
            max_guests = max(arch.guests[0], min(arch.guests[1], bedrooms * 2 + rng.randint(0, 2)))
            price = min(45000, max(1800, round(rng.uniform(*arch.price) / 100) * 100))
            cleaning = max(300, round(price * rng.uniform(0.03, 0.08) / 50) * 50)
            amenities = [
                *arch.must,
                *rng.sample(arch.may, k=min(len(arch.may), rng.randint(2, 5))),
                *[k for k, p in (("smoke_alarm", 0.85), ("first_aid_kit", 0.7), ("fire_extinguisher", 0.5)) if rng.random() < p],
            ]  # fmt: skip
            amenities = list(dict.fromkeys(amenities))
            listing = ListingModel(
                host_id=host.id, category_id=category_ids[arch.category],
                title=_title(rng, arch, taken_titles),
                description=_description(rng, arch, dest, amenities),
                property_type=arch.property_type, place_type=arch.place_type,
                address_line=f"{rng.randint(2, 98)}, {rng.choice(dest.streets)}",
                city=dest.city, state=dest.state, country="India", postal_code=dest.pin,
                latitude=round(dest.latitude + rng.uniform(-0.012, 0.012), 5),
                longitude=round(dest.longitude + rng.uniform(-0.012, 0.012), 5),
                price_per_night=price, cleaning_fee=cleaning,
                min_nights=rng.choices([1, 2, 3], weights=[60, 30, 10])[0], max_nights=30,
                max_guests=max_guests, bedrooms=bedrooms, beds=bedrooms + rng.randint(0, 2),
                bathrooms=min(bedrooms + 1, max(1, bedrooms - rng.randint(0, 1))) + rng.choice([0, 0, 0.5]),
                pets_allowed=stay_key in PET_FRIENDLY and rng.random() < 0.3,
                house_rules=" ".join(rng.sample(HOUSE_RULES, k=2)),
                check_in_time=rng.choice(["12:00", "13:00", "14:00", "15:00"]),
                check_out_time=rng.choice(["10:00", "11:00", "12:00"]),
                status="inactive" if counter == 9 else "active",  # one unlisted stay for the host demo
                created_at=now - timedelta(days=rng.randint(30, 420)), updated_at=now,
            )  # fmt: skip
            session.add(listing)
            session.flush()
            for position, (url, card_url) in enumerate(pick_photos(pools, arch.themes, counter)):
                session.add(
                    ListingPhotoModel(
                        listing_id=listing.id, url=url, card_url=card_url, position=position
                    )
                )
            session.add_all(
                ListingAmenityModel(listing_id=listing.id, amenity_id=amenity_ids[k])
                for k in amenities
            )
            infos.append(ListingInfo(listing.id, dest.host, host.id, price, cleaning,
                                     listing.min_nights, max_guests, listing.pets_allowed))  # fmt: skip
    session.flush()
    return infos
