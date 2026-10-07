"""Search filters. Each filter is a small class; `SqlListingReader` applies the registry in order,
so supporting a new filter means adding a class here, never editing the search code (Open/Closed).
The result count and the price histogram reuse the same registry, so they always agree."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import Select, Subquery, exists, func, or_, select

from app.adapters.sql.models import (
    AmenityModel,
    BookingModel,
    CategoryModel,
    ListingAmenityModel,
    ListingModel,
    UserModel,
)
from app.domain.enums import BookingStatus
from app.domain.listing_rules import FAVOURITE_MIN_RATING, FAVOURITE_MIN_REVIEWS
from app.schemas.listing import SearchParams


@dataclass(frozen=True)
class SearchContext:
    ratings: Subquery  # per-listing review aggregates: listing_id, avg, cnt


class ListingFilter(Protocol):
    def apply(self, stmt: Select, params: SearchParams, ctx: SearchContext) -> Select: ...


class LocationFilter:
    def apply(self, stmt, params, ctx):
        if not params.location:
            return stmt
        term = f"%{params.location.strip().lower()}%"
        return stmt.where(
            or_(
                func.lower(ListingModel.city).like(term),
                func.lower(ListingModel.state).like(term),
                func.lower(ListingModel.country).like(term),
            )
        )


class AvailabilityFilter:
    """Exclude listings with a confirmed booking overlapping the requested dates."""

    def apply(self, stmt, params, ctx):
        if params.check_in is None or params.check_out is None:
            return stmt
        clash = exists().where(
            BookingModel.listing_id == ListingModel.id,
            BookingModel.status == BookingStatus.CONFIRMED,
            BookingModel.check_in < params.check_out,
            BookingModel.check_out > params.check_in,
        )
        return stmt.where(~clash)


class GuestsFilter:
    def apply(self, stmt, params, ctx):
        if params.adults is not None:
            stmt = stmt.where(ListingModel.max_guests >= params.adults + params.children)
        if params.pets > 0:
            stmt = stmt.where(ListingModel.pets_allowed.is_(True))
        return stmt


class PriceFilter:
    def apply(self, stmt, params, ctx):
        if params.min_price is not None:
            stmt = stmt.where(ListingModel.price_per_night >= params.min_price)
        if params.max_price is not None:
            stmt = stmt.where(ListingModel.price_per_night <= params.max_price)
        return stmt


class PlaceAndPropertyTypeFilter:
    def apply(self, stmt, params, ctx):
        if params.place_type is not None:
            stmt = stmt.where(ListingModel.place_type == params.place_type)
        if params.property_types:
            stmt = stmt.where(ListingModel.property_type.in_(params.property_types))
        return stmt


class RoomsFilter:
    def apply(self, stmt, params, ctx):
        if params.bedrooms is not None:
            stmt = stmt.where(ListingModel.bedrooms >= params.bedrooms)
        if params.beds is not None:
            stmt = stmt.where(ListingModel.beds >= params.beds)
        if params.bathrooms is not None:
            stmt = stmt.where(ListingModel.bathrooms >= params.bathrooms)
        return stmt


class AmenitiesFilter:
    """A listing must offer every requested amenity (not just one of them)."""

    def apply(self, stmt, params, ctx):
        keys = set(params.amenities)
        if not keys:
            return stmt
        having_all = (
            select(ListingAmenityModel.listing_id)
            .join(AmenityModel, AmenityModel.id == ListingAmenityModel.amenity_id)
            .where(AmenityModel.key.in_(keys))
            .group_by(ListingAmenityModel.listing_id)
            .having(func.count(AmenityModel.id) == len(keys))
        )
        return stmt.where(ListingModel.id.in_(having_all))


class CategoryFilter:
    def apply(self, stmt, params, ctx):
        if not params.category:
            return stmt
        return stmt.where(
            ListingModel.category_id.in_(
                select(CategoryModel.id).where(CategoryModel.slug == params.category)
            )
        )


class HostBadgeFilter:
    def apply(self, stmt, params, ctx):
        if params.superhost:
            stmt = stmt.where(UserModel.is_superhost.is_(True))
        if params.guest_favourite:
            stmt = stmt.where(
                ctx.ratings.c.avg >= FAVOURITE_MIN_RATING,
                ctx.ratings.c.cnt >= FAVOURITE_MIN_REVIEWS,
            )
        return stmt


class BoundingBoxFilter:
    """Map view: only listings inside "south,west,north,east"."""

    def apply(self, stmt, params, ctx):
        if not params.bbox:
            return stmt
        try:
            south, west, north, east = (float(part) for part in params.bbox.split(","))
        except ValueError:
            return stmt
        return stmt.where(
            ListingModel.latitude.between(south, north), ListingModel.longitude.between(west, east)
        )


DEFAULT_FILTERS: tuple[ListingFilter, ...] = (
    LocationFilter(),
    AvailabilityFilter(),
    GuestsFilter(),
    PriceFilter(),
    PlaceAndPropertyTypeFilter(),
    RoomsFilter(),
    AmenitiesFilter(),
    CategoryFilter(),
    HostBadgeFilter(),
    BoundingBoxFilter(),
)
