from typing import Annotated

from fastapi import APIRouter, File, Query, Response, UploadFile

from app.core.container import HostServiceDep, HostUser, NoStore
from app.domain.errors import DomainError, ErrorKind
from app.schemas.host import HostListingOut, HostStatsOut, PhotoOrder, ReservationOut
from app.schemas.listing import ListingCreate, ListingDetailOut, ListingUpdate, PhotoOut
from app.services.media_service import MAX_UPLOAD_BYTES

router = APIRouter(prefix="/hosting", tags=["hosting"], dependencies=[NoStore])


@router.post("/listings", response_model=ListingDetailOut, status_code=201)
def create_listing(body: ListingCreate, host: HostUser, service: HostServiceDep):
    return service.create_listing(host, body.model_dump())


@router.get("/listings", response_model=list[HostListingOut])
def my_listings(host: HostUser, service: HostServiceDep):
    return service.listings(host)


@router.patch("/listings/{listing_id}", response_model=ListingDetailOut)
def update_listing(listing_id: int, body: ListingUpdate, host: HostUser, service: HostServiceDep):
    return service.update_listing(host, listing_id, body.model_dump(exclude_unset=True))


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(listing_id: int, host: HostUser, service: HostServiceDep):
    service.delete_listing(host, listing_id)
    return Response(status_code=204)


@router.post("/listings/{listing_id}/photos", response_model=PhotoOut, status_code=201)
async def upload_photo(
    listing_id: int,
    host: HostUser,
    service: HostServiceDep,
    file: Annotated[UploadFile, File()],
):
    data = await file.read(MAX_UPLOAD_BYTES + 1)  # one byte over the limit is enough to refuse
    if len(data) > MAX_UPLOAD_BYTES:
        raise DomainError(ErrorKind.BAD_REQUEST, "INVALID_IMAGE", "Images can be at most 5 MB.")
    return service.add_photo(host, listing_id, data)


# Declared before `/photos/{photo_id}` so "order" is not parsed as an id.
@router.put("/listings/{listing_id}/photos/order", response_model=list[PhotoOut])
def reorder_photos(listing_id: int, body: PhotoOrder, host: HostUser, service: HostServiceDep):
    return service.reorder_photos(host, listing_id, body.photo_ids)


@router.delete("/listings/{listing_id}/photos/{photo_id}", status_code=204)
def delete_photo(listing_id: int, photo_id: int, host: HostUser, service: HostServiceDep):
    service.remove_photo(host, listing_id, photo_id)
    return Response(status_code=204)


@router.get("/reservations", response_model=list[ReservationOut])
def reservations(
    host: HostUser,
    service: HostServiceDep,
    status: Annotated[str | None, Query(pattern="^(upcoming|past|cancelled)$")] = None,
):
    return service.reservations(host, status)


@router.get("/stats", response_model=HostStatsOut)
def stats(host: HostUser, service: HostServiceDep):
    return service.stats(host)
