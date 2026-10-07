from datetime import date

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.adapters.sql.models import (
    BookingModel,
    ListingModel,
    ListingPhotoModel,
    ReviewModel,
    UserModel,
)
from app.domain.entities import HostStats
from app.domain.enums import BookingStatus, ListingStatus
from app.schemas.host import HostListingOut, HostStatsOut, ReservationOut

CONFIRMED = BookingStatus.CONFIRMED


def _month_bounds(today: date) -> tuple[date, date]:
    start = today.replace(day=1)
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    return start, end


class SqlHostReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def listings(self, host_id: int, today: date) -> list[HostListingOut]:
        listings = self._session.scalars(
            select(ListingModel)
            .where(ListingModel.host_id == host_id)
            .order_by(ListingModel.created_at.desc(), ListingModel.id.desc())
        ).all()
        ids = [row.id for row in listings]
        ratings = {
            row.listing_id: (row.avg, row.cnt)
            for row in self._session.execute(
                select(
                    ReviewModel.listing_id,
                    func.avg(ReviewModel.rating).label("avg"),
                    func.count().label("cnt"),
                )
                .where(ReviewModel.listing_id.in_(ids))
                .group_by(ReviewModel.listing_id)
            )
        }
        upcoming = dict(
            self._session.execute(
                select(BookingModel.listing_id, func.count())
                .where(
                    BookingModel.listing_id.in_(ids),
                    BookingModel.status == CONFIRMED,
                    BookingModel.check_out >= today,
                )
                .group_by(BookingModel.listing_id)
            ).all()
        )
        covers: dict[int, str] = {}
        for photo in self._session.scalars(
            select(ListingPhotoModel)
            .where(ListingPhotoModel.listing_id.in_(ids))
            .order_by(ListingPhotoModel.listing_id, ListingPhotoModel.position)
        ):
            covers.setdefault(photo.listing_id, photo.card_url)
        return [
            HostListingOut(
                id=row.id,
                title=row.title,
                status=row.status,
                city=row.city,
                state=row.state,
                price_per_night=row.price_per_night,
                photo_url=covers.get(row.id),
                rating_avg=round(float(ratings[row.id][0]), 2) if row.id in ratings else None,
                review_count=ratings[row.id][1] if row.id in ratings else 0,
                upcoming_reservations=upcoming.get(row.id, 0),
            )
            for row in listings
        ]

    def reservations(self, host_id: int, today: date, scope: str | None) -> list[ReservationOut]:
        stmt = (
            select(BookingModel, ListingModel.title, UserModel)
            .join(ListingModel, ListingModel.id == BookingModel.listing_id)
            .join(UserModel, UserModel.id == BookingModel.guest_id)
            .where(ListingModel.host_id == host_id)
        )
        if scope == "upcoming":
            stmt = stmt.where(BookingModel.status == CONFIRMED, BookingModel.check_out >= today)
            stmt = stmt.order_by(BookingModel.check_in, BookingModel.id)
        else:
            if scope == "past":
                stmt = stmt.where(BookingModel.status == CONFIRMED, BookingModel.check_out < today)
            elif scope == "cancelled":
                stmt = stmt.where(BookingModel.status == BookingStatus.CANCELLED)
            stmt = stmt.order_by(BookingModel.check_in.desc(), BookingModel.id.desc())
        return [
            ReservationOut(
                code=booking.code,
                status=booking.status,
                listing_id=booking.listing_id,
                listing_title=title,
                guest_first_name=guest.first_name,
                guest_last_initial=guest.last_name[:1],
                guest_avatar_url=guest.avatar_url,
                check_in=booking.check_in,
                check_out=booking.check_out,
                nights=booking.nights,
                guests=booking.adults + booking.children,
                total=booking.total,
                payout=booking.subtotal + booking.cleaning_fee,
            )
            for booking, title, guest in self._session.execute(stmt).all()
        ]

    def stats(self, host_id: int, today: date) -> HostStatsOut:
        month_start, month_end = _month_bounds(today)
        payout = BookingModel.subtotal + BookingModel.cleaning_fee
        mine = and_(ListingModel.host_id == host_id, BookingModel.status == CONFIRMED)
        join = (BookingModel, ListingModel, ListingModel.id == BookingModel.listing_id)

        def total(*conditions) -> int:
            return (
                self._session.scalar(
                    select(func.coalesce(func.sum(payout), 0))
                    .select_from(join[0])
                    .join(join[1], join[2])
                    .where(mine, *conditions)
                )
                or 0
            )

        upcoming = self._session.scalar(
            select(func.count())
            .select_from(BookingModel)
            .join(ListingModel, ListingModel.id == BookingModel.listing_id)
            .where(mine, BookingModel.check_out >= today)
        )
        active = self._session.scalar(
            select(func.count()).where(
                ListingModel.host_id == host_id, ListingModel.status == ListingStatus.ACTIVE
            )
        )
        return HostStatsOut(
            active_listings=active or 0,
            upcoming_reservations=upcoming or 0,
            earnings_this_month=total(
                BookingModel.check_in >= month_start, BookingModel.check_in < month_end
            ),
            earnings_total=total(BookingModel.check_out < today),
        )

    def superhost_inputs(self, host_id: int, today: date) -> HostStats:
        avg_rating = self._session.scalar(
            select(func.avg(ReviewModel.rating))
            .join(ListingModel, ListingModel.id == ReviewModel.listing_id)
            .where(ListingModel.host_id == host_id)
        )
        completed, total_bookings, cancelled = self._session.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                and_(
                                    BookingModel.status == CONFIRMED, BookingModel.check_out < today
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.count(BookingModel.id),
                func.coalesce(
                    func.sum(case((BookingModel.status == BookingStatus.CANCELLED, 1), else_=0)), 0
                ),
            )
            .join(ListingModel, ListingModel.id == BookingModel.listing_id)
            .where(ListingModel.host_id == host_id)
        ).one()
        return HostStats(
            avg_rating=float(avg_rating) if avg_rating is not None else None,
            completed_stays=int(completed),
            total_bookings=int(total_bookings),
            cancelled_bookings=int(cancelled),
        )
