from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.adapters.sql.models import (
    AmenityModel,
    CategoryModel,
    ListingAmenityModel,
    ListingModel,
    ListingPhotoModel,
    ReviewModel,
    UserModel,
)
from app.adapters.sql.search_filters import (
    DEFAULT_FILTERS,
    ListingFilter,
    PriceFilter,
    SearchContext,
)
from app.domain.enums import ListingStatus
from app.domain.listing_rules import is_guest_favourite
from app.schemas.common import Page
from app.schemas.listing import (
    AmenityOut,
    CategoryOut,
    DestinationOut,
    ListingCardOut,
    ListingDetailOut,
    ListingSummaryOut,
    LocationSuggestion,
    PhotoOut,
    PhotoRef,
    PriceHistogramOut,
    RatingBreakdown,
    SearchParams,
)
from app.schemas.user import HostProfileOut

CARD_PHOTOS = 5
HISTOGRAM_BUCKETS = 20


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 2)


class SqlListingReader:
    def __init__(
        self, session: Session, filters: Sequence[ListingFilter] = DEFAULT_FILTERS
    ) -> None:
        self._session = session
        self._filters = filters

    # ---------- search ----------

    def _ratings(self):
        return (
            select(
                ReviewModel.listing_id.label("listing_id"),
                func.avg(ReviewModel.rating).label("avg"),
                func.count(ReviewModel.id).label("cnt"),
            )
            .group_by(ReviewModel.listing_id)
            .subquery()
        )

    def _base(self, active_only: bool = True) -> tuple[Select, SearchContext]:
        ratings = self._ratings()
        stmt = (
            select(ListingModel, UserModel.is_superhost, ratings.c.avg, ratings.c.cnt)
            .join(UserModel, UserModel.id == ListingModel.host_id)
            .outerjoin(ratings, ratings.c.listing_id == ListingModel.id)
        )
        if active_only:
            stmt = stmt.where(ListingModel.status == ListingStatus.ACTIVE)
        return stmt, SearchContext(ratings)

    def _filtered(self, params: SearchParams, filters: Sequence[ListingFilter] | None = None):
        stmt, ctx = self._base()
        for listing_filter in filters if filters is not None else self._filters:
            stmt = listing_filter.apply(stmt, params, ctx)
        return stmt, ctx

    def search(self, params: SearchParams) -> Page[ListingCardOut]:
        stmt, ctx = self._filtered(params)
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rating = func.coalesce(ctx.ratings.c.avg, 0)
        order = {
            "price_asc": [ListingModel.price_per_night.asc(), ListingModel.id],
            "price_desc": [ListingModel.price_per_night.desc(), ListingModel.id],
            "newest": [ListingModel.created_at.desc(), ListingModel.id.desc()],
            "rating": [rating.desc(), ListingModel.id],
        }.get(
            params.sort,
            [rating.desc(), func.coalesce(ctx.ratings.c.cnt, 0).desc(), ListingModel.id],
        )
        rows = self._session.execute(
            stmt.order_by(*order)
            .limit(params.page_size)
            .offset((params.page - 1) * params.page_size)
        ).all()
        return Page(
            items=self._cards_from_rows(rows),
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    def price_histogram(self, params: SearchParams) -> PriceHistogramOut:
        """Price distribution of everything that matches *except* the price filter itself, so the
        slider keeps showing the full range while the guest drags it."""
        others = [f for f in self._filters if not isinstance(f, PriceFilter)]
        stmt, _ = self._filtered(params, others)
        prices = [row[0].price_per_night for row in self._session.execute(stmt).all()]
        if not prices:
            return PriceHistogramOut(min_price=0, max_price=0, buckets=[0] * HISTOGRAM_BUCKETS)
        low, high = min(prices), max(prices)
        width = (high - low) / HISTOGRAM_BUCKETS or 1
        buckets = [0] * HISTOGRAM_BUCKETS
        for price in prices:
            buckets[min(int((price - low) / width), HISTOGRAM_BUCKETS - 1)] += 1
        return PriceHistogramOut(min_price=low, max_price=high, buckets=buckets)

    def cards(self, listing_ids: list[int]) -> list[ListingCardOut]:
        if not listing_ids:
            return []
        stmt, _ = self._base()
        rows = self._session.execute(stmt.where(ListingModel.id.in_(listing_ids))).all()
        by_id = {card.id: card for card in self._cards_from_rows(rows)}
        return [by_id[i] for i in listing_ids if i in by_id]

    def _photos_by_listing(self, listing_ids: list[int]) -> dict[int, list[PhotoOut]]:
        photos: dict[int, list[PhotoOut]] = {i: [] for i in listing_ids}
        rows = self._session.scalars(
            select(ListingPhotoModel)
            .where(ListingPhotoModel.listing_id.in_(listing_ids))
            .order_by(ListingPhotoModel.listing_id, ListingPhotoModel.position)
        )
        for row in rows:
            photos[row.listing_id].append(
                PhotoOut(
                    id=row.id,
                    url=row.url,
                    card_url=row.card_url,
                    caption=row.caption,
                    position=row.position,
                )
            )
        return photos

    def _card(self, row, avg, cnt, host_is_superhost, photos: list[PhotoOut]) -> ListingCardOut:
        rating_avg = _round(avg)
        count = int(cnt or 0)
        return ListingCardOut(
            id=row.id,
            title=row.title,
            city=row.city,
            state=row.state,
            property_type=row.property_type,
            place_type=row.place_type,
            price_per_night=row.price_per_night,
            cleaning_fee=row.cleaning_fee,
            max_guests=row.max_guests,
            bedrooms=row.bedrooms,
            beds=row.beds,
            bathrooms=row.bathrooms,
            rating_avg=rating_avg,
            review_count=count,
            is_guest_favourite=is_guest_favourite(rating_avg, count),
            host_is_superhost=bool(host_is_superhost),
            photos=[PhotoRef(url=p.url, card_url=p.card_url) for p in photos[:CARD_PHOTOS]],
            latitude=row.latitude,
            longitude=row.longitude,
        )

    def _cards_from_rows(self, rows) -> list[ListingCardOut]:
        photos = self._photos_by_listing([row[0].id for row in rows]) if rows else {}
        return [self._card(r[0], r[2], r[3], r[1], photos[r[0].id]) for r in rows]

    # ---------- detail ----------

    def get_detail(self, listing_id: int) -> ListingDetailOut | None:
        stmt, _ = self._base(active_only=False)
        found = self._session.execute(stmt.where(ListingModel.id == listing_id)).first()
        if found is None:
            return None
        row, host_is_superhost, avg, cnt = found
        photos = self._photos_by_listing([listing_id])[listing_id]
        card = self._card(row, avg, cnt, host_is_superhost, photos)

        category = self._session.get(CategoryModel, row.category_id)
        amenities = self._session.scalars(
            select(AmenityModel)
            .join(ListingAmenityModel, ListingAmenityModel.amenity_id == AmenityModel.id)
            .where(ListingAmenityModel.listing_id == listing_id)
            .order_by(AmenityModel.id)
        ).all()
        host = self._session.get(UserModel, row.host_id)

        sums = self._session.execute(
            select(
                func.avg(ReviewModel.cleanliness),
                func.avg(ReviewModel.accuracy),
                func.avg(ReviewModel.check_in),
                func.avg(ReviewModel.communication),
                func.avg(ReviewModel.location),
                func.avg(ReviewModel.value),
            ).where(ReviewModel.listing_id == listing_id)
        ).one()
        distribution = {stars: 0 for stars in range(5, 0, -1)}
        distribution.update(
            dict(
                self._session.execute(
                    select(ReviewModel.rating, func.count())
                    .where(ReviewModel.listing_id == listing_id)
                    .group_by(ReviewModel.rating)
                ).all()
            )
        )
        return ListingDetailOut(
            **card.model_dump(),
            status=row.status,
            description=row.description,
            country=row.country,
            category=CategoryOut.model_validate(category),
            amenities=[AmenityOut.model_validate(a) for a in amenities],
            all_photos=photos,
            host=HostProfileOut.model_validate(host),
            house_rules=row.house_rules,
            min_nights=row.min_nights,
            max_nights=row.max_nights,
            pets_allowed=row.pets_allowed,
            check_in_time=row.check_in_time,
            check_out_time=row.check_out_time,
            rating_breakdown=RatingBreakdown(
                **dict(
                    zip(
                        (
                            "cleanliness",
                            "accuracy",
                            "check_in",
                            "communication",
                            "location",
                            "value",
                        ),
                        (_round(v) for v in sums),
                        strict=True,
                    )
                )
            ),
            rating_distribution=distribution,
            address_line=row.address_line,
            postal_code=row.postal_code,
        )

    # ---------- small lookups ----------

    def summaries(self, listing_ids: list[int]) -> dict[int, ListingSummaryOut]:
        if not listing_ids:
            return {}
        rows = self._session.execute(
            select(ListingModel, UserModel.first_name)
            .join(UserModel, UserModel.id == ListingModel.host_id)
            .where(ListingModel.id.in_(listing_ids))
        ).all()
        photos = self._photos_by_listing(list({r[0].id for r in rows}))
        return {
            listing.id: ListingSummaryOut(
                id=listing.id,
                title=listing.title,
                city=listing.city,
                state=listing.state,
                photo_url=photos[listing.id][0].card_url if photos[listing.id] else None,
                host_first_name=host_first_name,
            )
            for listing, host_first_name in rows
        }

    def categories(self) -> list[CategoryOut]:
        rows = self._session.scalars(
            select(CategoryModel).order_by(CategoryModel.sort_order, CategoryModel.id)
        )
        return [CategoryOut.model_validate(r) for r in rows]

    def amenities(self) -> list[AmenityOut]:
        rows = self._session.scalars(select(AmenityModel).order_by(AmenityModel.id))
        return [AmenityOut.model_validate(r) for r in rows]

    def suggest_locations(self, query: str, limit: int = 8) -> list[LocationSuggestion]:
        term = f"%{query.strip().lower()}%"
        rows = self._session.execute(
            select(ListingModel.city, ListingModel.state)
            .where(
                ListingModel.status == ListingStatus.ACTIVE,
                (func.lower(ListingModel.city).like(term))
                | (func.lower(ListingModel.state).like(term)),
            )
            .group_by(ListingModel.city, ListingModel.state)
            .order_by(func.count().desc(), ListingModel.city)
            .limit(limit)
        ).all()
        return [
            LocationSuggestion(
                label=f"{city}, {state}" if city != state else f"{state}, India",
                city=city,
                state=state,
            )
            for city, state in rows
        ]

    def destinations(self, limit: int = 20) -> list[DestinationOut]:
        rows = self._session.execute(
            select(
                ListingModel.city,
                ListingModel.state,
                func.count().label("n"),
                func.min(ListingModel.id).label("first_id"),
            )
            .where(ListingModel.status == ListingStatus.ACTIVE)
            .group_by(ListingModel.city, ListingModel.state)
            .order_by(func.count().desc(), ListingModel.city)
            .limit(limit)
        ).all()
        covers = {
            photo.listing_id: photo.card_url
            for photo in self._session.scalars(
                select(ListingPhotoModel).where(
                    ListingPhotoModel.listing_id.in_([r.first_id for r in rows]),
                    ListingPhotoModel.position == 0,
                )
            )
        }
        return [
            DestinationOut(
                city=r.city, state=r.state, listing_count=r.n, cover_url=covers.get(r.first_id)
            )
            for r in rows
        ]
