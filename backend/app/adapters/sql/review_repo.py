from dataclasses import asdict

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.sql.models import ReviewModel, UserModel
from app.domain.entities import NewReview, Review
from app.domain.errors import DomainError, ErrorKind
from app.schemas.common import Page
from app.schemas.review import ReviewOut


def to_review(row: ReviewModel) -> Review:
    return Review(
        id=row.id,
        booking_id=row.booking_id,
        listing_id=row.listing_id,
        author_id=row.author_id,
        rating=row.rating,
        cleanliness=row.cleanliness,
        accuracy=row.accuracy,
        check_in=row.check_in,
        communication=row.communication,
        location=row.location,
        value=row.value,
        comment=row.comment,
        created_at=row.created_at,
    )


class SqlReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, new: NewReview) -> Review:
        row = ReviewModel(**asdict(new))
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise DomainError(
                ErrorKind.CONFLICT, "REVIEW_EXISTS", "You already reviewed this stay."
            ) from exc
        return to_review(row)

    def reviewed_booking_ids(self, booking_ids: list[int]) -> set[int]:
        if not booking_ids:
            return set()
        rows = self._session.scalars(
            select(ReviewModel.booking_id).where(ReviewModel.booking_id.in_(booking_ids))
        )
        return set(rows)

    def list_for_listing(self, listing_id: int, page: int, page_size: int) -> Page[ReviewOut]:
        total = self._session.scalar(
            select(func.count())
            .select_from(ReviewModel)
            .where(ReviewModel.listing_id == listing_id)
        )
        rows = self._session.execute(
            select(ReviewModel, UserModel)
            .join(UserModel, UserModel.id == ReviewModel.author_id)
            .where(ReviewModel.listing_id == listing_id)
            .order_by(ReviewModel.created_at.desc(), ReviewModel.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
        items = [
            ReviewOut(
                id=review.id,
                author_first_name=author.first_name,
                author_last_initial=author.last_name[:1],
                author_avatar_url=author.avatar_url,
                rating=review.rating,
                cleanliness=review.cleanliness,
                accuracy=review.accuracy,
                check_in=review.check_in,
                communication=review.communication,
                location=review.location,
                value=review.value,
                comment=review.comment,
                created_at=review.created_at,
            )
            for review, author in rows
        ]
        return Page(items=items, page=page, page_size=page_size, total=total or 0)
