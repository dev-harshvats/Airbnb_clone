from app.domain.errors import DomainError, ErrorKind
from app.ports.uow import UnitOfWork
from app.schemas.catalog import (
    CatalogSearchParams,
    ExperienceCardOut,
    ExperienceDetailOut,
    ServiceCardOut,
    ServiceDetailOut,
    ServiceTypeOut,
)
from app.schemas.common import Page


class CatalogService:
    """The Experiences and Services tabs: browsing hosted activities and local professionals."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def search_experiences(self, params: CatalogSearchParams) -> Page[ExperienceCardOut]:
        return self._uow.experience_reader.search(params)

    def experience(self, experience_id: int) -> ExperienceDetailOut:
        found = self._uow.experience_reader.get_detail(experience_id)
        if found is None:
            raise DomainError(ErrorKind.NOT_FOUND, "EXPERIENCE_NOT_FOUND", "Experience not found.")
        return found

    def search_services(self, params: CatalogSearchParams) -> Page[ServiceCardOut]:
        return self._uow.service_reader.search(params)

    def service(self, service_id: int) -> ServiceDetailOut:
        found = self._uow.service_reader.get_detail(service_id)
        if found is None:
            raise DomainError(ErrorKind.NOT_FOUND, "SERVICE_NOT_FOUND", "Service not found.")
        return found

    def service_types(self, location: str | None) -> list[ServiceTypeOut]:
        return self._uow.service_reader.types(location)
