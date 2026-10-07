from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.sql.models.mixins import now_column, string_enum
from app.core.database import Base
from app.domain.enums import AmenityGroup, ListingStatus, PlaceType


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True)
    label: Mapped[str] = mapped_column(String(60))
    icon_key: Mapped[str] = mapped_column(String(40))
    sort_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))


class AmenityModel(Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    icon_key: Mapped[str] = mapped_column(String(40))
    group: Mapped[AmenityGroup] = mapped_column(string_enum(AmenityGroup, "amenity_group"))


class ListingModel(Base):
    __tablename__ = "listings"
    __table_args__ = (
        CheckConstraint("price_per_night > 0", name="price_positive"),
        CheckConstraint("cleaning_fee >= 0", name="cleaning_fee_non_negative"),
        CheckConstraint("max_guests > 0", name="max_guests_positive"),
        CheckConstraint("min_nights >= 1", name="min_nights_positive"),
        CheckConstraint("max_nights >= min_nights", name="max_nights_not_below_min"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
        CheckConstraint(
            "bedrooms >= 0 AND beds >= 0 AND bathrooms >= 0", name="rooms_non_negative"
        ),
        Index("ix_listings_status_city", "status", "city"),
        Index("ix_listings_price_per_night", "price_per_night"),
        Index("ix_listings_category_id", "category_id"),
        Index("ix_listings_host_id", "host_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    property_type: Mapped[str] = mapped_column(String(40))
    place_type: Mapped[PlaceType] = mapped_column(string_enum(PlaceType, "place_type"))
    address_line: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    country: Mapped[str] = mapped_column(String(80), default="India", server_default="India")
    postal_code: Mapped[str] = mapped_column(String(12))
    latitude: Mapped[float]
    longitude: Mapped[float]
    price_per_night: Mapped[int]  # whole rupees
    cleaning_fee: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    min_nights: Mapped[int] = mapped_column(default=1, server_default=text("1"))
    max_nights: Mapped[int] = mapped_column(default=90, server_default=text("90"))
    max_guests: Mapped[int]
    bedrooms: Mapped[int]
    beds: Mapped[int]
    bathrooms: Mapped[float] = mapped_column(Numeric(3, 1, asdecimal=False))
    pets_allowed: Mapped[bool] = mapped_column(default=False, server_default=text("0"))
    house_rules: Mapped[str] = mapped_column(Text, default="", server_default="")
    check_in_time: Mapped[str] = mapped_column(String(5), default="15:00", server_default="15:00")
    check_out_time: Mapped[str] = mapped_column(String(5), default="11:00", server_default="11:00")
    status: Mapped[ListingStatus] = mapped_column(
        string_enum(ListingStatus, "listing_status"),
        default=ListingStatus.DRAFT,
        server_default=ListingStatus.DRAFT.value,
    )
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class ListingPhotoModel(Base):
    __tablename__ = "listing_photos"
    __table_args__ = (
        UniqueConstraint("listing_id", "position", name="uq_listing_photos_listing_id_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(500))  # full-size (1440px) rendition
    card_url: Mapped[str] = mapped_column(String(500))  # card-size (720px) rendition
    caption: Mapped[str | None] = mapped_column(String(200))
    position: Mapped[int]


class ListingAmenityModel(Base):
    __tablename__ = "listing_amenities"

    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    amenity_id: Mapped[int] = mapped_column(
        ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True
    )
