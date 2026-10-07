from typing import Annotated

from fastapi import APIRouter, Query

from app.core.container import CatalogServiceDep
from app.schemas.catalog import (
    CatalogSearchParams,
    ServiceCardOut,
    ServiceDetailOut,
    ServiceTypeOut,
)
from app.schemas.common import Page

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=Page[ServiceCardOut])
def search_services(params: Annotated[CatalogSearchParams, Query()], service: CatalogServiceDep):
    return service.search_services(params)


# Declared before `/{service_id}` so "types" is not parsed as an id.
@router.get("/types", response_model=list[ServiceTypeOut])
def service_types(
    service: CatalogServiceDep, location: Annotated[str | None, Query(max_length=100)] = None
):
    return service.service_types(location)


@router.get("/{service_id}", response_model=ServiceDetailOut)
def service_detail(service_id: int, service: CatalogServiceDep):
    return service.service(service_id)
