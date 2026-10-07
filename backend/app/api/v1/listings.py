from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.container import ListingServiceDep, OptionalUser, SearchServiceDep
from app.schemas.common import Page
from app.schemas.listing import (
    AvailabilityOut,
    ListingCardOut,
    ListingDetailOut,
    PriceHistogramOut,
    QuoteOut,
    QuoteRequest,
    SearchParams,
)
from app.schemas.review import ReviewOut

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=Page[ListingCardOut])
def search_listings(params: Annotated[SearchParams, Query()], service: SearchServiceDep):
    return service.search(params)


# Declared before `/{listing_id}` so "price-histogram" is not parsed as an id.
@router.get("/price-histogram", response_model=PriceHistogramOut)
def price_histogram(params: Annotated[SearchParams, Query()], service: SearchServiceDep):
    return service.price_histogram(params)


@router.get("/{listing_id}", response_model=ListingDetailOut)
def listing_detail(listing_id: int, viewer: OptionalUser, service: ListingServiceDep):
    return service.detail(listing_id, viewer)


@router.get("/{listing_id}/availability", response_model=AvailabilityOut)
def availability(
    listing_id: int,
    service: ListingServiceDep,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
):
    return service.availability(listing_id, start, end)


@router.post("/{listing_id}/quote", response_model=QuoteOut)
def quote(listing_id: int, body: QuoteRequest, service: ListingServiceDep):
    return service.quote(listing_id, body.check_in, body.check_out)


@router.get("/{listing_id}/reviews", response_model=Page[ReviewOut])
def listing_reviews(
    listing_id: int,
    service: ListingServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
):
    return service.reviews(listing_id, page, page_size)
