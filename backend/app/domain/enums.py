"""Closed vocabularies shared by the domain, the database constraints and the API."""

from enum import StrEnum


class PlaceType(StrEnum):
    ENTIRE = "entire"
    PRIVATE_ROOM = "private_room"
    SHARED_ROOM = "shared_room"


class ListingStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"


class BookingStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    CARD = "card"
    UPI = "upi"


class AmenityGroup(StrEnum):
    ESSENTIALS = "essentials"
    FEATURES = "features"
    SAFETY = "safety"
    LOCATION = "location"


class ExperienceCategory(StrEnum):
    FOOD = "food"
    HERITAGE = "heritage"
    ADVENTURE = "adventure"
    WELLNESS = "wellness"
    NATURE = "nature"
    ARTS = "arts"


class ServiceType(StrEnum):
    PHOTOGRAPHY = "photography"
    CHEFS = "chefs"
    TRAINING = "training"
    MAKEUP = "makeup"
    HAIR = "hair"
    MASSAGE = "massage"
