from typing import Annotated

from fastapi import APIRouter, Header, Query

from app.core.container import BookingServiceDep, CurrentUser, NoStore, ReviewServiceDep
from app.schemas.booking import BookingCreate, BookingOut, TripScope
from app.schemas.review import ReviewCreate

router = APIRouter(prefix="/bookings", tags=["bookings"], dependencies=[NoStore])


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(
    body: BookingCreate,
    user: CurrentUser,
    service: BookingServiceDep,
    idempotency_key: Annotated[str | None, Header(max_length=64)] = None,
):
    # A retry with the same Idempotency-Key returns the original booking (also 201).
    booking, _created = service.create(user, body, idempotency_key)
    return booking


@router.get("", response_model=list[BookingOut])
def my_trips(
    user: CurrentUser,
    service: BookingServiceDep,
    scope: Annotated[TripScope, Query()] = "upcoming",
):
    return service.trips(user, scope)


@router.get("/{code}", response_model=BookingOut)
def get_booking(code: str, user: CurrentUser, service: BookingServiceDep):
    return service.get(user, code)


@router.post("/{code}/cancel", response_model=BookingOut)
def cancel_booking(code: str, user: CurrentUser, service: BookingServiceDep):
    return service.cancel(user, code)


@router.post("/{code}/review", status_code=201)
def review_stay(code: str, body: ReviewCreate, user: CurrentUser, service: ReviewServiceDep):
    service.review_stay(user, code, body)
    return {"status": "created"}
