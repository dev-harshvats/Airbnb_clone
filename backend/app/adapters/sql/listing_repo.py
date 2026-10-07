from dataclasses import fields
from datetime import datetime

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.sql.models import (
    BookingModel,
    ListingAmenityModel,
    ListingModel,
    ListingPhotoModel,
)
from app.domain.entities import Listing, ListingFields
from app.domain.errors import DomainError, ErrorKind
from app.schemas.listing import PhotoOut

_FIELD_NAMES = [f.name for f in fields(ListingFields)]


def to_listing(row: ListingModel) -> Listing:
    return Listing(
        id=row.id,
        host_id=row.host_id,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        **{name: getattr(row, name) for name in _FIELD_NAMES},
    )


def to_photo(row: ListingPhotoModel) -> PhotoOut:
    return PhotoOut(
        id=row.id, url=row.url, card_url=row.card_url, caption=row.caption, position=row.position
    )


def _invalid_reference() -> DomainError:
    return DomainError(ErrorKind.BAD_REQUEST, "INVALID_REFERENCE", "Unknown category or amenity.")


class SqlListingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, listing_id: int) -> Listing | None:
        row = self._session.get(ListingModel, listing_id)
        return to_listing(row) if row else None

    def add(self, host_id, fields_: ListingFields, amenity_ids, when: datetime) -> Listing:
        row = ListingModel(
            host_id=host_id,
            created_at=when,
            updated_at=when,
            **{name: getattr(fields_, name) for name in _FIELD_NAMES},
        )
        self._session.add(row)
        try:
            self._session.flush()
            self._set_amenities(row.id, amenity_ids)
        except IntegrityError as exc:
            self._session.rollback()
            raise _invalid_reference() from exc
        return to_listing(row)

    def update(self, listing: Listing, amenity_ids, when: datetime) -> Listing:
        row = self._session.get(ListingModel, listing.id)
        for name in _FIELD_NAMES:
            setattr(row, name, getattr(listing, name))
        row.status = listing.status
        row.updated_at = when
        try:
            self._session.flush()
            if amenity_ids is not None:
                self._set_amenities(row.id, amenity_ids)
        except IntegrityError as exc:
            self._session.rollback()
            raise _invalid_reference() from exc
        return to_listing(row)

    def _set_amenities(self, listing_id: int, amenity_ids: list[int]) -> None:
        self._session.execute(
            delete(ListingAmenityModel).where(ListingAmenityModel.listing_id == listing_id)
        )
        self._session.add_all(
            ListingAmenityModel(listing_id=listing_id, amenity_id=a) for a in set(amenity_ids)
        )
        self._session.flush()

    def delete(self, listing_id: int) -> None:
        # The database cascades photos, amenities and wishlist items.
        self._session.execute(delete(ListingModel).where(ListingModel.id == listing_id))

    def has_bookings(self, listing_id: int) -> bool:
        return bool(
            self._session.scalar(select(exists().where(BookingModel.listing_id == listing_id)))
        )

    # ---------- photos ----------

    def photos(self, listing_id: int) -> list[PhotoOut]:
        rows = self._session.scalars(
            select(ListingPhotoModel)
            .where(ListingPhotoModel.listing_id == listing_id)
            .order_by(ListingPhotoModel.position)
        )
        return [to_photo(r) for r in rows]

    def add_photo(self, listing_id: int, url: str, card_url: str) -> PhotoOut:
        last = self._session.scalar(
            select(func.max(ListingPhotoModel.position)).where(
                ListingPhotoModel.listing_id == listing_id
            )
        )
        row = ListingPhotoModel(
            listing_id=listing_id,
            url=url,
            card_url=card_url,
            position=0 if last is None else last + 1,
        )
        self._session.add(row)
        self._session.flush()
        return to_photo(row)

    def remove_photo(self, listing_id: int, photo_id: int) -> PhotoOut | None:
        row = self._session.scalar(
            select(ListingPhotoModel).where(
                ListingPhotoModel.id == photo_id, ListingPhotoModel.listing_id == listing_id
            )
        )
        if row is None:
            return None
        removed = to_photo(row)
        self._session.delete(row)
        self._session.flush()
        return removed

    def reorder_photos(self, listing_id: int, photo_ids: list[int]) -> None:
        # Two passes so the UNIQUE(listing_id, position) constraint is never violated midway.
        for offset, photo_id in enumerate(photo_ids):
            self._set_position(listing_id, photo_id, -1 - offset)
        for position, photo_id in enumerate(photo_ids):
            self._set_position(listing_id, photo_id, position)

    def _set_position(self, listing_id: int, photo_id: int, position: int) -> None:
        self._session.execute(
            update(ListingPhotoModel)
            .where(ListingPhotoModel.id == photo_id, ListingPhotoModel.listing_id == listing_id)
            .values(position=position)
        )
