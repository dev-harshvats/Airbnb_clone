from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import BookingStatus, PaymentMethod
from app.schemas.listing import ListingSummaryOut


class BookingCreate(BaseModel):
    listing_id: int
    check_in: date
    check_out: date
    adults: int = Field(ge=1, le=16)
    children: int = Field(default=0, ge=0, le=16)
    infants: int = Field(default=0, ge=0, le=5)
    pets: int = Field(default=0, ge=0, le=5)
    payment_method: PaymentMethod  # mocked: nothing is charged or stored

    @model_validator(mode="after")
    def _ordered(self) -> "BookingCreate":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class BookingOut(BaseModel):
    code: str
    status: BookingStatus
    listing: ListingSummaryOut
    check_in: date
    check_out: date
    adults: int
    children: int
    infants: int
    pets: int
    nights: int
    nightly_rate: int
    subtotal: int
    cleaning_fee: int
    service_fee: int
    taxes: int
    total: int
    payment_method: PaymentMethod
    created_at: datetime
    cancelled_at: datetime | None
    can_cancel: bool  # before check-in, while confirmed
    can_review: bool  # completed and not yet reviewed
    has_review: bool


TripScope = Literal["upcoming", "past", "cancelled"]
