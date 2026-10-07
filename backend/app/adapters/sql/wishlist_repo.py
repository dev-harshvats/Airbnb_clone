from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.sql.models import (
    ListingModel,
    ListingPhotoModel,
    WishlistItemModel,
    WishlistModel,
)
from app.domain.entities import Wishlist
from app.domain.errors import DomainError, ErrorKind
from app.schemas.wishlist import WishlistOut


def to_wishlist(row: WishlistModel) -> Wishlist:
    return Wishlist(id=row.id, user_id=row.user_id, name=row.name, created_at=row.created_at)


class SqlWishlistRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, user_id: int, name: str, when: datetime) -> Wishlist:
        row = WishlistModel(user_id=user_id, name=name, created_at=when)
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise DomainError(
                ErrorKind.CONFLICT, "WISHLIST_EXISTS", "You already have a wishlist with that name."
            ) from exc
        return to_wishlist(row)

    def get(self, wishlist_id: int, user_id: int) -> Wishlist | None:
        row = self._session.scalar(
            select(WishlistModel).where(
                WishlistModel.id == wishlist_id, WishlistModel.user_id == user_id
            )
        )
        return to_wishlist(row) if row else None

    def list_for_user(self, user_id: int) -> list[WishlistOut]:
        out = []
        for wishlist in self._session.scalars(
            select(WishlistModel)
            .where(WishlistModel.user_id == user_id)
            .order_by(WishlistModel.created_at.desc(), WishlistModel.id.desc())
        ):
            ids = self.listing_ids(wishlist.id)
            cover = None
            if ids:  # the first saved listing's first photo is the wishlist cover
                cover = self._session.scalar(
                    select(ListingPhotoModel.card_url)
                    .where(ListingPhotoModel.listing_id == ids[0])
                    .order_by(ListingPhotoModel.position)
                    .limit(1)
                )
            out.append(
                WishlistOut(
                    id=wishlist.id, name=wishlist.name, item_count=len(ids), cover_url=cover
                )
            )
        return out

    def listing_ids(self, wishlist_id: int) -> list[int]:
        return list(
            self._session.scalars(
                select(WishlistItemModel.listing_id)
                .where(WishlistItemModel.wishlist_id == wishlist_id)
                .order_by(WishlistItemModel.created_at, WishlistItemModel.listing_id)
            )
        )

    def saved_listing_ids(self, user_id: int) -> list[int]:
        return list(
            self._session.scalars(
                select(WishlistItemModel.listing_id)
                .join(WishlistModel, WishlistModel.id == WishlistItemModel.wishlist_id)
                .where(WishlistModel.user_id == user_id)
                .group_by(WishlistItemModel.listing_id)
                .order_by(func.max(WishlistItemModel.created_at).desc())
            )
        )

    def add_item(self, wishlist_id: int, listing_id: int, when: datetime) -> None:
        if self._session.get(ListingModel, listing_id) is None:
            raise DomainError(ErrorKind.NOT_FOUND, "LISTING_NOT_FOUND", "Listing not found.")
        if self._session.get(WishlistItemModel, (wishlist_id, listing_id)) is None:
            self._session.add(
                WishlistItemModel(wishlist_id=wishlist_id, listing_id=listing_id, created_at=when)
            )
            self._session.flush()

    def remove_item(self, wishlist_id: int, listing_id: int) -> None:
        self._session.execute(
            delete(WishlistItemModel).where(
                WishlistItemModel.wishlist_id == wishlist_id,
                WishlistItemModel.listing_id == listing_id,
            )
        )

    def delete(self, wishlist_id: int) -> None:
        self._session.execute(delete(WishlistModel).where(WishlistModel.id == wishlist_id))
