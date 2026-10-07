from collections.abc import Sequence

from app.domain.booking_policy import nights_between
from app.domain.pricing import FeeRule, calculate_quote
from app.ports.uow import UnitOfWork
from app.schemas.common import Page
from app.schemas.listing import (
    AmenityOut,
    CategoryOut,
    DestinationOut,
    ListingCardOut,
    LocationSuggestion,
    PriceHistogramOut,
    SearchParams,
)


class SearchService:
    """Browsing: search results, the price histogram and the reference data behind the filters."""

    def __init__(self, uow: UnitOfWork, fee_rules: Sequence[FeeRule]) -> None:
        self._uow = uow
        self._fee_rules = fee_rules

    def search(self, params: SearchParams) -> Page[ListingCardOut]:
        page = self._uow.listing_reader.search(params)
        if params.check_in and params.check_out:  # show "₹X total" for the chosen dates
            nights = nights_between(params.check_in, params.check_out)
            for card in page.items:
                card.total_for_dates = calculate_quote(
                    card.price_per_night, card.cleaning_fee, nights, self._fee_rules
                ).total
        return page

    def price_histogram(self, params: SearchParams) -> PriceHistogramOut:
        return self._uow.listing_reader.price_histogram(params)

    def categories(self) -> list[CategoryOut]:
        return self._uow.listing_reader.categories()

    def amenities(self) -> list[AmenityOut]:
        return self._uow.listing_reader.amenities()

    def suggest_locations(self, query: str) -> list[LocationSuggestion]:
        return self._uow.listing_reader.suggest_locations(query) if query.strip() else []

    def destinations(self) -> list[DestinationOut]:
        return self._uow.listing_reader.destinations()
