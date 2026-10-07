from fastapi import APIRouter, Response

from app.core.container import CurrentUser, NoStore, WishlistServiceDep
from app.schemas.wishlist import SavedIdsOut, WishlistCreate, WishlistDetailOut, WishlistOut

router = APIRouter(prefix="/wishlists", tags=["wishlists"], dependencies=[NoStore])


@router.get("", response_model=list[WishlistOut])
def my_wishlists(user: CurrentUser, service: WishlistServiceDep):
    return service.list(user)


@router.post("", response_model=WishlistOut, status_code=201)
def create_wishlist(body: WishlistCreate, user: CurrentUser, service: WishlistServiceDep):
    return service.create(user, body.name)


# Declared before `/{wishlist_id}` so "saved-ids" is not parsed as an id.
@router.get("/saved-ids", response_model=SavedIdsOut)
def saved_ids(user: CurrentUser, service: WishlistServiceDep):
    """Every listing the user has saved, in any wishlist (drives the filled-in heart icons)."""
    return service.saved_ids(user)


@router.get("/{wishlist_id}", response_model=WishlistDetailOut)
def wishlist_detail(wishlist_id: int, user: CurrentUser, service: WishlistServiceDep):
    return service.detail(user, wishlist_id)


@router.delete("/{wishlist_id}", status_code=204)
def delete_wishlist(wishlist_id: int, user: CurrentUser, service: WishlistServiceDep):
    service.delete(user, wishlist_id)
    return Response(status_code=204)


@router.put("/{wishlist_id}/items/{listing_id}", status_code=204)
def save_listing(wishlist_id: int, listing_id: int, user: CurrentUser, service: WishlistServiceDep):
    service.add(user, wishlist_id, listing_id)
    return Response(status_code=204)


@router.delete("/{wishlist_id}/items/{listing_id}", status_code=204)
def unsave_listing(
    wishlist_id: int, listing_id: int, user: CurrentUser, service: WishlistServiceDep
):
    service.remove(user, wishlist_id, listing_id)
    return Response(status_code=204)
