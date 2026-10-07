from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain.enums import ListingStatus, PlaceType
from app.schemas.user import HostProfileOut

Sort = Literal["recommended", "price_asc", "price_desc", "rating", "newest"]
Time = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]


# ---------- read models ----------


class PhotoRef(BaseModel):
    url: str
    card_url: str


class PhotoOut(PhotoRef):
    id: int
    caption: str | None = None
    position: int


class AmenityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    icon_key: str
    group: str


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    icon_key: str


class ListingCardOut(BaseModel):
    id: int
    title: str
    city: str
    state: str
    property_type: str
    place_type: PlaceType
    price_per_night: int
    cleaning_fee: int
    max_guests: int
    bedrooms: int
    beds: int
    bathrooms: float
    rating_avg: float | None
    review_count: int
    is_guest_favourite: bool
    host_is_superhost: bool
    photos: list[PhotoRef]
    latitude: float
    longitude: float
    total_for_dates: int | None = None  # set when the search included dates


class RatingBreakdown(BaseModel):
    cleanliness: float | None
    accuracy: float | None
    check_in: float | None
    communication: float | None
    location: float | None
    value: float | None


class ListingDetailOut(ListingCardOut):
    status: ListingStatus
    description: str
    country: str
    category: CategoryOut
    amenities: list[AmenityOut]
    all_photos: list[PhotoOut]
    host: HostProfileOut
    house_rules: str
    min_nights: int
    max_nights: int
    pets_allowed: bool
    check_in_time: str
    check_out_time: str
    rating_breakdown: RatingBreakdown
    rating_distribution: dict[int, int]  # stars -> number of reviews
    # Only returned to the listing's own host:
    address_line: str | None = None
    postal_code: str | None = None


class ListingSummaryOut(BaseModel):
    """The slice of a listing shown on trip and reservation cards."""

    id: int
    title: str
    city: str
    state: str
    photo_url: str | None
    host_first_name: str


class DateRange(BaseModel):
    check_in: date
    check_out: date


class AvailabilityOut(BaseModel):
    booked: list[DateRange]


class PriceHistogramOut(BaseModel):
    min_price: int
    max_price: int
    buckets: list[int]  # listing counts per equal-width price band


class LocationSuggestion(BaseModel):
    label: str  # "Goa, India"
    city: str
    state: str


class DestinationOut(BaseModel):
    """A place guests can browse: its city, how many stays it has, and a cover photo."""

    city: str
    state: str
    listing_count: int
    cover_url: str | None


class QuoteRequest(BaseModel):
    check_in: date
    check_out: date


class QuoteOut(BaseModel):
    nightly_rate: int
    nights: int
    subtotal: int
    cleaning_fee: int
    service_fee: int
    taxes: int
    total: int


# ---------- search ----------


class SearchParams(BaseModel):
    """Query string of GET /listings. Every filter is optional."""

    location: str | None = Field(default=None, max_length=100)
    check_in: date | None = None
    check_out: date | None = None
    adults: int | None = Field(default=None, ge=1, le=16)
    children: int = Field(default=0, ge=0, le=16)
    pets: int = Field(default=0, ge=0, le=5)
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    place_type: PlaceType | None = None
    property_types: list[str] = []
    bedrooms: int | None = Field(default=None, ge=0)
    beds: int | None = Field(default=None, ge=0)
    bathrooms: float | None = Field(default=None, ge=0)
    amenities: list[str] = []  # amenity keys; a listing must have all of them
    category: str | None = None  # category slug
    superhost: bool = False
    guest_favourite: bool = False
    bbox: str | None = Field(default=None, description="south,west,north,east")
    sort: Sort = "recommended"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=50)

    @model_validator(mode="after")
    def _dates_come_as_a_pair(self) -> "SearchParams":
        if (self.check_in is None) != (self.check_out is None):
            raise ValueError("check_in and check_out must be given together")
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


# ---------- host input ----------

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Rupees = Annotated[int, Field(gt=0, le=1_000_000)]


class ListingCreate(BaseModel):
    """A new listing, always saved as a draft; publish with PATCH status=active."""

    model_config = ConfigDict(extra="forbid")

    category_id: int
    title: Title
    description: Text
    property_type: str
    place_type: PlaceType
    address_line: Short
    city: Short
    state: Short
    country: Short = "India"
    postal_code: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=12)
    ]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    price_per_night: Rupees
    cleaning_fee: int = Field(default=0, ge=0, le=100_000)
    min_nights: int = Field(default=1, ge=1, le=30)
    max_nights: int = Field(default=90, ge=1, le=365)
    max_guests: int = Field(ge=1, le=16)
    bedrooms: int = Field(ge=0, le=50)
    beds: int = Field(ge=0, le=50)
    bathrooms: float = Field(ge=0, le=50)
    pets_allowed: bool = False
    house_rules: Text = ""
    check_in_time: Time = "15:00"
    check_out_time: Time = "11:00"
    amenity_ids: list[int] = []


class ListingUpdate(BaseModel):
    """Partial update: only the fields that are sent change."""

    model_config = ConfigDict(extra="forbid")

    category_id: int | None = None
    title: Title | None = None
    description: Text | None = None
    property_type: str | None = None
    place_type: PlaceType | None = None
    address_line: Short | None = None
    city: Short | None = None
    state: Short | None = None
    country: Short | None = None
    postal_code: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=12)] | None
    ) = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    price_per_night: Rupees | None = None
    cleaning_fee: int | None = Field(default=None, ge=0, le=100_000)
    min_nights: int | None = Field(default=None, ge=1, le=30)
    max_nights: int | None = Field(default=None, ge=1, le=365)
    max_guests: int | None = Field(default=None, ge=1, le=16)
    bedrooms: int | None = Field(default=None, ge=0, le=50)
    beds: int | None = Field(default=None, ge=0, le=50)
    bathrooms: float | None = Field(default=None, ge=0, le=50)
    pets_allowed: bool | None = None
    house_rules: Text | None = None
    check_in_time: Time | None = None
    check_out_time: Time | None = None
    status: ListingStatus | None = None
    amenity_ids: list[int] | None = None
