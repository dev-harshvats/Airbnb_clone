"""Importing this package registers every table on `Base.metadata` (used by Alembic)."""

from app.adapters.sql.models.booking import BookingModel
from app.adapters.sql.models.catalog import (
    ExperienceModel,
    ExperiencePhotoModel,
    ServiceModel,
    ServicePhotoModel,
)
from app.adapters.sql.models.listing import (
    AmenityModel,
    CategoryModel,
    ListingAmenityModel,
    ListingModel,
    ListingPhotoModel,
)
from app.adapters.sql.models.review import ReviewModel
from app.adapters.sql.models.user import RefreshTokenModel, UserModel
from app.adapters.sql.models.wishlist import WishlistItemModel, WishlistModel

__all__ = [
    "AmenityModel",
    "BookingModel",
    "CategoryModel",
    "ExperienceModel",
    "ExperiencePhotoModel",
    "ListingAmenityModel",
    "ListingModel",
    "ListingPhotoModel",
    "RefreshTokenModel",
    "ReviewModel",
    "ServiceModel",
    "ServicePhotoModel",
    "UserModel",
    "WishlistItemModel",
    "WishlistModel",
]
