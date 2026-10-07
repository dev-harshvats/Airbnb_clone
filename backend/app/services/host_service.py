from dataclasses import fields, replace

from app.domain.entities import Listing, ListingFields, User
from app.domain.enums import ListingStatus
from app.domain.errors import DomainError, ErrorKind
from app.domain.listing_rules import (
    MAX_PHOTOS,
    ensure_publishable,
    validate_listing_fields,
)
from app.ports.clock import Clock
from app.ports.uow import UnitOfWork
from app.schemas.host import HostListingOut, HostStatsOut, ReservationOut
from app.schemas.listing import ListingDetailOut, PhotoOut
from app.services.listing_service import listing_not_found
from app.services.media_service import MediaService

_EDITABLE = {f.name for f in fields(ListingFields)}


class HostService:
    """What a host can do: manage their listings and photos, and see reservations and earnings."""

    def __init__(self, uow: UnitOfWork, clock: Clock, media: MediaService) -> None:
        self._uow = uow
        self._clock = clock
        self._media = media

    # ---------- listings ----------

    def create_listing(self, host: User, data: dict) -> ListingDetailOut:
        amenity_ids = data.pop("amenity_ids", [])
        listing_fields = ListingFields(**data)
        validate_listing_fields(listing_fields)
        listing = self._uow.listings.add(host.id, listing_fields, amenity_ids, self._clock.now())
        self._uow.commit()
        return self._uow.listing_reader.get_detail(listing.id)

    def update_listing(self, host: User, listing_id: int, changes: dict) -> ListingDetailOut:
        listing = self._own_listing(host, listing_id)
        amenity_ids = changes.pop("amenity_ids", None)
        status = changes.pop("status", None)
        updated = replace(listing, **{k: v for k, v in changes.items() if k in _EDITABLE})
        validate_listing_fields(updated)
        if status is not None:
            if status == ListingStatus.ACTIVE:
                ensure_publishable(len(self._uow.listings.photos(listing_id)))
            updated = replace(updated, status=status)
        self._uow.listings.update(updated, amenity_ids, self._clock.now())
        self._uow.commit()
        return self._uow.listing_reader.get_detail(listing_id)

    def delete_listing(self, host: User, listing_id: int) -> None:
        """Only a listing that was never booked can be deleted: bookings are guests' records.
        Everything else should be unlisted (status=inactive) instead."""
        self._own_listing(host, listing_id)
        if self._uow.listings.has_bookings(listing_id):
            raise DomainError(
                ErrorKind.CONFLICT,
                "LISTING_HAS_BOOKINGS",
                "This listing has bookings and cannot be deleted. Unlist it instead.",
            )
        photos = self._uow.listings.photos(listing_id)
        self._uow.listings.delete(listing_id)
        self._uow.commit()
        for photo in photos:  # files are removed only after the delete is safely committed
            self._media.discard(photo.url, photo.card_url)

    # ---------- photos ----------

    def add_photo(self, host: User, listing_id: int, data: bytes) -> PhotoOut:
        self._own_listing(host, listing_id)
        if len(self._uow.listings.photos(listing_id)) >= MAX_PHOTOS:
            raise DomainError(
                ErrorKind.BAD_REQUEST,
                "TOO_MANY_PHOTOS",
                f"A listing can have at most {MAX_PHOTOS} photos.",
            )
        url, card_url = self._media.store_image(data)
        try:
            photo = self._uow.listings.add_photo(listing_id, url, card_url)
            self._uow.commit()
        except Exception:
            self._media.discard(url, card_url)  # the files exist but no row points at them
            raise
        return photo

    def remove_photo(self, host: User, listing_id: int, photo_id: int) -> None:
        listing = self._own_listing(host, listing_id)
        photos = self._uow.listings.photos(listing_id)
        if photo_id not in {p.id for p in photos}:
            raise DomainError(ErrorKind.NOT_FOUND, "PHOTO_NOT_FOUND", "Photo not found.")
        if listing.status == ListingStatus.ACTIVE:
            ensure_publishable(len(photos) - 1)  # a live listing must keep enough photos
        removed = self._uow.listings.remove_photo(listing_id, photo_id)
        self._uow.commit()
        self._media.discard(removed.url, removed.card_url)

    def reorder_photos(self, host: User, listing_id: int, photo_ids: list[int]) -> list[PhotoOut]:
        self._own_listing(host, listing_id)
        if sorted(photo_ids) != sorted(p.id for p in self._uow.listings.photos(listing_id)):
            raise DomainError(
                ErrorKind.BAD_REQUEST,
                "INVALID_PHOTO_ORDER",
                "List every photo of the listing once.",
            )
        self._uow.listings.reorder_photos(listing_id, photo_ids)
        self._uow.commit()
        return self._uow.listings.photos(listing_id)

    # ---------- dashboard ----------

    def listings(self, host: User) -> list[HostListingOut]:
        return self._uow.host_reader.listings(host.id, self._clock.today())

    def reservations(self, host: User, scope: str | None) -> list[ReservationOut]:
        return self._uow.host_reader.reservations(host.id, self._clock.today(), scope)

    def stats(self, host: User) -> HostStatsOut:
        return self._uow.host_reader.stats(host.id, self._clock.today())

    # ---------- helpers ----------

    def _own_listing(self, host: User, listing_id: int) -> Listing:
        listing = self._uow.listings.get(listing_id)
        if listing is None:
            raise listing_not_found()
        if listing.host_id != host.id:
            raise DomainError(ErrorKind.FORBIDDEN, "NOT_OWNER", "This is not your listing.")
        return listing
