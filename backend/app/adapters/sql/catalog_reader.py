from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.adapters.sql.models import (
    ExperienceModel,
    ExperiencePhotoModel,
    ServiceModel,
    ServicePhotoModel,
    UserModel,
)
from app.domain.enums import ListingStatus, ServiceType
from app.schemas.catalog import (
    CatalogSearchParams,
    ExperienceCardOut,
    ExperienceDetailOut,
    ServiceCardOut,
    ServiceDetailOut,
    ServiceTypeOut,
)
from app.schemas.common import Page
from app.schemas.listing import PhotoOut, PhotoRef
from app.schemas.user import HostProfileOut

CARD_PHOTOS = 5
SERVICE_LABELS = {
    ServiceType.PHOTOGRAPHY: "Photography",
    ServiceType.CHEFS: "Chefs",
    ServiceType.TRAINING: "Training",
    ServiceType.MAKEUP: "Make-up",
    ServiceType.HAIR: "Hair",
    ServiceType.MASSAGE: "Massage",
}


def _rating(value: float | None) -> float | None:
    return None if value is None else round(float(value), 2)


def _where_location(stmt: Select, model, location: str | None) -> Select:
    if not location:
        return stmt
    term = f"%{location.strip().lower()}%"
    return stmt.where((func.lower(model.city).like(term)) | (func.lower(model.state).like(term)))


def _photos(
    session: Session, photo_model, owner_column, ids: list[int]
) -> dict[int, list[PhotoOut]]:
    photos: dict[int, list[PhotoOut]] = {i: [] for i in ids}
    if not ids:
        return photos
    rows = session.scalars(
        select(photo_model)
        .where(owner_column.in_(ids))
        .order_by(owner_column, photo_model.position)
    )
    for row in rows:
        owner = getattr(row, owner_column.key)
        photos[owner].append(
            PhotoOut(id=row.id, url=row.url, card_url=row.card_url, position=row.position)
        )
    return photos


def _refs(photos: list[PhotoOut]) -> list[PhotoRef]:
    return [PhotoRef(url=p.url, card_url=p.card_url) for p in photos[:CARD_PHOTOS]]


class SqlExperienceReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, params: CatalogSearchParams) -> Page[ExperienceCardOut]:
        stmt = select(ExperienceModel).where(ExperienceModel.status == ListingStatus.ACTIVE)
        stmt = _where_location(stmt, ExperienceModel, params.location)
        if params.category:
            stmt = stmt.where(ExperienceModel.category == params.category)
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rating = func.coalesce(ExperienceModel.rating_avg, 0)
        order = {
            "price_asc": [ExperienceModel.price_per_guest, ExperienceModel.id],
            "price_desc": [ExperienceModel.price_per_guest.desc(), ExperienceModel.id],
            "rating": [rating.desc(), ExperienceModel.id],
        }.get(params.sort, [rating.desc(), ExperienceModel.review_count.desc(), ExperienceModel.id])
        rows = self._session.scalars(
            stmt.order_by(*order)
            .limit(params.page_size)
            .offset((params.page - 1) * params.page_size)
        ).all()
        photos = _photos(
            self._session,
            ExperiencePhotoModel,
            ExperiencePhotoModel.experience_id,
            [r.id for r in rows],
        )
        return Page(
            items=[self._card(r, photos[r.id]) for r in rows],
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    def get_detail(self, experience_id: int) -> ExperienceDetailOut | None:
        row = self._session.get(ExperienceModel, experience_id)
        if row is None or row.status != ListingStatus.ACTIVE:
            return None
        photos = _photos(
            self._session, ExperiencePhotoModel, ExperiencePhotoModel.experience_id, [row.id]
        )[row.id]
        host = self._session.get(UserModel, row.host_id)
        return ExperienceDetailOut(
            **self._card(row, photos).model_dump(),
            description=row.description,
            max_guests=row.max_guests,
            latitude=row.latitude,
            longitude=row.longitude,
            all_photos=photos,
            host=HostProfileOut.model_validate(host),
        )

    @staticmethod
    def _card(row: ExperienceModel, photos: list[PhotoOut]) -> ExperienceCardOut:
        return ExperienceCardOut(
            id=row.id,
            title=row.title,
            category=row.category,
            city=row.city,
            state=row.state,
            start_time=row.start_time,
            duration_minutes=row.duration_minutes,
            price_per_guest=row.price_per_guest,
            rating_avg=_rating(row.rating_avg),
            review_count=row.review_count,
            photos=_refs(photos),
        )


class SqlServiceReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, params: CatalogSearchParams) -> Page[ServiceCardOut]:
        stmt = select(ServiceModel).where(ServiceModel.status == ListingStatus.ACTIVE)
        stmt = _where_location(stmt, ServiceModel, params.location)
        if params.service_type:
            stmt = stmt.where(ServiceModel.service_type == params.service_type)
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rating = func.coalesce(ServiceModel.rating_avg, 0)
        order = {
            "price_asc": [ServiceModel.price_from, ServiceModel.id],
            "price_desc": [ServiceModel.price_from.desc(), ServiceModel.id],
            "rating": [rating.desc(), ServiceModel.id],
        }.get(params.sort, [ServiceModel.is_popular.desc(), rating.desc(), ServiceModel.id])
        rows = self._session.scalars(
            stmt.order_by(*order)
            .limit(params.page_size)
            .offset((params.page - 1) * params.page_size)
        ).all()
        photos = _photos(
            self._session, ServicePhotoModel, ServicePhotoModel.service_id, [r.id for r in rows]
        )
        return Page(
            items=[self._card(r, photos[r.id]) for r in rows],
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    def get_detail(self, service_id: int) -> ServiceDetailOut | None:
        row = self._session.get(ServiceModel, service_id)
        if row is None or row.status != ListingStatus.ACTIVE:
            return None
        photos = _photos(self._session, ServicePhotoModel, ServicePhotoModel.service_id, [row.id])[
            row.id
        ]
        host = self._session.get(UserModel, row.host_id)
        return ServiceDetailOut(
            **self._card(row, photos).model_dump(),
            description=row.description,
            all_photos=photos,
            host=HostProfileOut.model_validate(host),
        )

    def types(self, location: str | None) -> list[ServiceTypeOut]:
        stmt = select(ServiceModel.service_type, func.count()).where(
            ServiceModel.status == ListingStatus.ACTIVE
        )
        stmt = _where_location(stmt, ServiceModel, location).group_by(ServiceModel.service_type)
        counts = dict(self._session.execute(stmt).all())
        return [  # in a fixed, familiar order rather than by count
            ServiceTypeOut(key=kind, label=SERVICE_LABELS[kind], count=counts[kind])
            for kind in ServiceType
            if kind in counts
        ]

    @staticmethod
    def _card(row: ServiceModel, photos: list[PhotoOut]) -> ServiceCardOut:
        return ServiceCardOut(
            id=row.id,
            title=row.title,
            service_type=row.service_type,
            city=row.city,
            state=row.state,
            price_from=row.price_from,
            price_unit=row.price_unit,
            is_popular=row.is_popular,
            rating_avg=_rating(row.rating_avg),
            review_count=row.review_count,
            photos=_refs(photos),
        )
