"""Experiences and services for the demo: hosted activities and local professionals.

All titles and descriptions are original demo copy. Ratings are stored on each row (mocked), since
these two tabs are browse-only in this version."""

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.adapters.sql.models import (
    ExperienceModel,
    ExperiencePhotoModel,
    ServiceModel,
    ServicePhotoModel,
    UserModel,
)
from app.seed.builder import pick_photos
from app.seed.destinations import DESTINATIONS

# city, title, category, photo themes, start time, minutes, price range (rupees per guest)
EXPERIENCES = [
    (
        "Jaipur",
        "Old City heritage walk with a local historian",
        "heritage",
        ("heritage", "interior"),
        "08:30",
        150,
        (900, 1800),
    ),
    (
        "Jaipur",
        "Block-printing workshop in a family studio",
        "arts",
        ("heritage", "interior"),
        "11:00",
        180,
        (1200, 2400),
    ),
    (
        "Jaipur",
        "Rooftop thali and Pink City sunset",
        "food",
        ("heritage", "interior"),
        "17:30",
        120,
        (1500, 2800),
    ),
    (
        "Udaipur",
        "Sunset boat ride and lake-side storytelling",
        "nature",
        ("heritage", "backwaters"),
        "17:00",
        90,
        (1100, 2200),
    ),
    (
        "Udaipur",
        "Miniature painting masterclass",
        "arts",
        ("heritage", "interior"),
        "10:00",
        150,
        (1300, 2600),
    ),
    (
        "Jaisalmer",
        "Dune sunset with folk music and dinner",
        "adventure",
        ("desert", "cabin"),
        "16:30",
        240,
        (1800, 3600),
    ),
    (
        "Anjuna",
        "Spice-farm lunch and cooking class",
        "food",
        ("estate", "beach"),
        "10:30",
        210,
        (1600, 3200),
    ),
    (
        "Anjuna",
        "Sunrise paddleboarding and beach breakfast",
        "adventure",
        ("beach", "pool"),
        "06:30",
        120,
        (1400, 2600),
    ),
    (
        "Palolem",
        "Kayaking to Butterfly Beach",
        "adventure",
        ("beach", "cabin"),
        "07:00",
        180,
        (1500, 2800),
    ),
    (
        "Mumbai",
        "Street-food trail through Colaba and Fort",
        "food",
        ("city", "heritage"),
        "17:00",
        180,
        (1200, 2400),
    ),
    (
        "Mumbai",
        "Dawn photo walk along Marine Drive",
        "arts",
        ("city", "heritage"),
        "06:00",
        150,
        (1000, 2000),
    ),
    (
        "Manali",
        "Himalayan foothills day trek with a guide",
        "adventure",
        ("hills", "cabin"),
        "08:00",
        360,
        (1600, 3000),
    ),
    (
        "Shimla",
        "Colonial heritage walk and chai tasting",
        "heritage",
        ("hills", "estate"),
        "09:30",
        150,
        (800, 1600),
    ),
    (
        "Leh",
        "Monastery trail and butter-tea morning",
        "heritage",
        ("ladakh", "interior"),
        "09:00",
        240,
        (1500, 2800),
    ),
    (
        "Rishikesh",
        "Sunrise yoga by the Ganga",
        "wellness",
        ("spiritual", "hills"),
        "06:00",
        90,
        (500, 1200),
    ),
    (
        "Rishikesh",
        "Evening aarti and ghat walk",
        "heritage",
        ("spiritual",),
        "17:30",
        120,
        (600, 1400),
    ),
    (
        "Varanasi",
        "Dawn boat ride along the ghats",
        "heritage",
        ("spiritual", "heritage"),
        "05:30",
        120,
        (900, 1800),
    ),
    (
        "Alleppey",
        "Canoe ride through village backwaters",
        "nature",
        ("backwaters", "estate"),
        "08:00",
        150,
        (900, 1800),
    ),
    (
        "Alleppey",
        "Kerala home-cooked meal with a local family",
        "food",
        ("backwaters", "interior"),
        "12:30",
        120,
        (1200, 2200),
    ),
    (
        "Kochi",
        "Fort Kochi heritage and spice-market walk",
        "heritage",
        ("city", "heritage"),
        "09:00",
        150,
        (900, 1800),
    ),
    (
        "Munnar",
        "Tea-estate walk and tasting",
        "nature",
        ("hills", "estate"),
        "09:30",
        150,
        (800, 1600),
    ),
    (
        "Coorg",
        "Coffee plantation tour and tasting",
        "food",
        ("estate", "hills"),
        "10:00",
        150,
        (900, 1800),
    ),
    (
        "Bengaluru",
        "Filter-coffee and dosa breakfast trail",
        "food",
        ("city", "interior"),
        "07:30",
        150,
        (800, 1600),
    ),
    (
        "Pondicherry",
        "French Quarter cycling tour",
        "heritage",
        ("beach", "heritage"),
        "07:00",
        150,
        (700, 1500),
    ),
    (
        "Gokarna",
        "Cliff-top beach trek and sunset picnic",
        "adventure",
        ("beach", "cabin"),
        "15:30",
        210,
        (1000, 2200),
    ),
    (
        "Darjeeling",
        "Tea-garden sunrise and toy-train ride",
        "nature",
        ("hills", "estate"),
        "05:30",
        240,
        (1100, 2200),
    ),
]

# city, title, type, photo themes, price from, unit
SERVICES = [
    (
        "Jaipur",
        "Couple and family portraits at Amber Fort",
        "photography",
        ("heritage", "city"),
        6500,
        "session",
    ),
    (
        "Udaipur",
        "Lake-palace pre-wedding photoshoot",
        "photography",
        ("heritage", "backwaters"),
        12000,
        "session",
    ),
    (
        "Anjuna",
        "Beach-sunset portraits and short reels",
        "photography",
        ("beach", "pool"),
        5500,
        "session",
    ),
    (
        "Manali",
        "Mountain-view couple photography",
        "photography",
        ("hills", "cabin"),
        6000,
        "session",
    ),
    (
        "Mumbai",
        "Candid street and skyline portraits",
        "photography",
        ("city", "heritage"),
        7000,
        "session",
    ),
    (
        "Anjuna",
        "Goan seafood private chef at your villa",
        "chefs",
        ("beach", "pool"),
        3500,
        "guest",
    ),
    ("Jaipur", "Rajasthani thali by a home chef", "chefs", ("heritage", "interior"), 2200, "guest"),
    (
        "Kochi",
        "Kerala sadya and seafood private dining",
        "chefs",
        ("backwaters", "city"),
        2800,
        "guest",
    ),
    ("Mumbai", "Tasting-menu chef at home", "chefs", ("city", "interior"), 4500, "guest"),
    (
        "Rishikesh",
        "Private yoga and meditation sessions",
        "training",
        ("spiritual", "hills"),
        1800,
        "session",
    ),
    ("Bengaluru", "Personal training at your stay", "training", ("city", "interior"), 2000, "hour"),
    (
        "Goa",
        "Surf and fitness coaching on the beach",
        "training",
        ("beach", "cabin"),
        2500,
        "session",
    ),
    ("Mumbai", "Bridal and party make-up artist", "makeup", ("city", "interior"), 5500, "session"),
    (
        "Jaipur",
        "Festive make-up with traditional looks",
        "makeup",
        ("heritage", "interior"),
        4000,
        "session",
    ),
    (
        "Bengaluru",
        "Studio-quality party make-up at home",
        "makeup",
        ("city", "interior"),
        3500,
        "session",
    ),
    ("Mumbai", "Hair styling for events and shoots", "hair", ("city", "interior"), 2500, "session"),
    (
        "Jaipur",
        "Braids, updos and blow-dry at your door",
        "hair",
        ("heritage", "interior"),
        1800,
        "session",
    ),
    (
        "Alleppey",
        "Ayurvedic massage on the houseboat",
        "massage",
        ("backwaters", "interior"),
        2500,
        "session",
    ),
    (
        "Munnar",
        "Aromatherapy massage in the tea hills",
        "massage",
        ("hills", "interior"),
        2200,
        "session",
    ),
    (
        "Rishikesh",
        "Deep-tissue and sound-bath therapy",
        "massage",
        ("spiritual", "interior"),
        2000,
        "session",
    ),
]

_EXPERIENCE_OPENERS = {
    "food": "Eat your way through the local flavours with someone who knows every kitchen.",
    "heritage": "Walk through layers of history with a guide who grew up here.",
    "adventure": "Get outdoors with an experienced local and all the gear you need.",
    "wellness": "Slow down and reset with a calm, guided session.",
    "nature": "Spend a few unhurried hours with the landscape and the people who live in it.",
    "arts": "Make something by hand, guided by a working artist.",
}


def _destination(city: str):
    return next((d for d in DESTINATIONS if d.city == city), DESTINATIONS[0])


def _rating(rng: random.Random) -> tuple[float | None, int]:
    if rng.random() < 0.08:
        return None, 0  # a brand-new listing with no reviews yet
    return round(rng.uniform(4.6, 5.0), 2), rng.randint(6, 240)


def create_experiences(
    session: Session, rng: random.Random, users: dict[str, UserModel], pools, now: datetime
) -> int:
    for index, (city, title, category, themes, start, minutes, price) in enumerate(EXPERIENCES, 1):
        dest = _destination(city)
        rating, reviews = _rating(rng)
        row = ExperienceModel(
            host_id=users[dest.host].id, title=title, category=category, city=dest.city,
            state=dest.state, latitude=round(dest.latitude + rng.uniform(-0.01, 0.01), 5),
            longitude=round(dest.longitude + rng.uniform(-0.01, 0.01), 5), start_time=start,
            duration_minutes=minutes, price_per_guest=round(rng.uniform(*price) / 50) * 50,
            max_guests=rng.choice([4, 6, 8, 10, 12]), rating_avg=rating, review_count=reviews,
            description=(
                f"{_EXPERIENCE_OPENERS[category]} Meet your host in {dest.city}, {dest.state}, "
                f"and spend about {minutes // 60 or 1} hour{'s' if minutes >= 120 else ''} together. "
                "Small groups, local tips and no rush."
            ),
            created_at=now - timedelta(days=rng.randint(20, 300)),
        )  # fmt: skip
        session.add(row)
        session.flush()
        for position, (url, card_url) in enumerate(pick_photos(pools, themes, index)):
            session.add(
                ExperiencePhotoModel(
                    experience_id=row.id, url=url, card_url=card_url, position=position
                )
            )
    return len(EXPERIENCES)


def create_services(
    session: Session, rng: random.Random, users: dict[str, UserModel], pools, now: datetime
) -> int:
    for index, (city, title, kind, themes, price, unit) in enumerate(SERVICES, 1):
        dest = _destination(city)
        rating, reviews = _rating(rng)
        row = ServiceModel(
            host_id=users[dest.host].id, title=title, service_type=kind, city=dest.city,
            state=dest.state, price_from=price, price_unit=unit, is_popular=rng.random() < 0.3,
            rating_avg=rating, review_count=reviews,
            description=(
                f"{title}. Based in {dest.city}, {dest.state}, and happy to come to your stay. "
                "Share what you have in mind and your host will tailor the session around it."
            ),
            created_at=now - timedelta(days=rng.randint(20, 300)),
        )  # fmt: skip
        session.add(row)
        session.flush()
        for position, (url, card_url) in enumerate(pick_photos(pools, themes, index + 3)):
            session.add(
                ServicePhotoModel(service_id=row.id, url=url, card_url=card_url, position=position)
            )
    return len(SERVICES)
