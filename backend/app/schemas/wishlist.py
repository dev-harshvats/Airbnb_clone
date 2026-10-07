from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.schemas.listing import ListingCardOut


class WishlistCreate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class WishlistOut(BaseModel):
    id: int
    name: str
    item_count: int
    cover_url: str | None


class WishlistDetailOut(BaseModel):
    id: int
    name: str
    listings: list[ListingCardOut]


class SavedIdsOut(BaseModel):
    listing_ids: list[int]
