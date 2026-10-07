"""Experiences and services (the other two tabs of the site): read models and search filters."""

from typing import Literal

from pydantic import BaseModel, Field

from app.domain.enums import ExperienceCategory, ServiceType
from app.schemas.listing import PhotoOut, PhotoRef
from app.schemas.user import HostProfileOut

CatalogSort = Literal["recommended", "price_asc", "price_desc", "rating"]


class CatalogSearchParams(BaseModel):
    """Query string of GET /experiences and GET /services."""

    location: str | None = Field(default=None, max_length=100)
    category: ExperienceCategory | None = None  # experiences only
    service_type: ServiceType | None = None  # services only
    sort: CatalogSort = "recommended"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=50)


class ExperienceCardOut(BaseModel):
    id: int
    title: str
    category: ExperienceCategory
    city: str
    state: str
    start_time: str  # HH:MM
    duration_minutes: int
    price_per_guest: int
    rating_avg: float | None
    review_count: int
    photos: list[PhotoRef]


class ExperienceDetailOut(ExperienceCardOut):
    description: str
    max_guests: int
    latitude: float
    longitude: float
    all_photos: list[PhotoOut]
    host: HostProfileOut


class ServiceCardOut(BaseModel):
    id: int
    title: str
    service_type: ServiceType
    city: str
    state: str
    price_from: int
    price_unit: str
    is_popular: bool
    rating_avg: float | None
    review_count: int
    photos: list[PhotoRef]


class ServiceDetailOut(ServiceCardOut):
    description: str
    all_photos: list[PhotoOut]
    host: HostProfileOut


class ServiceTypeOut(BaseModel):
    """A service category tile ("Photography") with how many services it has."""

    key: ServiceType
    label: str
    count: int
