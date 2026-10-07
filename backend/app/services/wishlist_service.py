from app.domain.entities import User, Wishlist
from app.domain.errors import DomainError, ErrorKind
from app.ports.clock import Clock
from app.ports.uow import UnitOfWork
from app.schemas.wishlist import SavedIdsOut, WishlistDetailOut, WishlistOut


class WishlistService:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def list(self, user: User) -> list[WishlistOut]:
        return self._uow.wishlists.list_for_user(user.id)

    def saved_ids(self, user: User) -> SavedIdsOut:
        return SavedIdsOut(listing_ids=self._uow.wishlists.saved_listing_ids(user.id))

    def create(self, user: User, name: str) -> WishlistOut:
        wishlist = self._uow.wishlists.create(user.id, name, self._clock.now())
        self._uow.commit()
        return WishlistOut(id=wishlist.id, name=wishlist.name, item_count=0, cover_url=None)

    def detail(self, user: User, wishlist_id: int) -> WishlistDetailOut:
        wishlist = self._own(user, wishlist_id)
        ids = self._uow.wishlists.listing_ids(wishlist.id)
        return WishlistDetailOut(
            id=wishlist.id, name=wishlist.name, listings=self._uow.listing_reader.cards(ids)
        )

    def delete(self, user: User, wishlist_id: int) -> None:
        self._uow.wishlists.delete(self._own(user, wishlist_id).id)
        self._uow.commit()

    def add(self, user: User, wishlist_id: int, listing_id: int) -> None:
        wishlist = self._own(user, wishlist_id)
        self._uow.wishlists.add_item(wishlist.id, listing_id, self._clock.now())
        self._uow.commit()

    def remove(self, user: User, wishlist_id: int, listing_id: int) -> None:
        wishlist = self._own(user, wishlist_id)
        self._uow.wishlists.remove_item(wishlist.id, listing_id)
        self._uow.commit()

    def _own(self, user: User, wishlist_id: int) -> Wishlist:
        wishlist = self._uow.wishlists.get(wishlist_id, user.id)
        if wishlist is None:  # also hides other people's wishlists
            raise DomainError(ErrorKind.NOT_FOUND, "WISHLIST_NOT_FOUND", "Wishlist not found.")
        return wishlist
