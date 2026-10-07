from typing import Annotated

from fastapi import APIRouter, Query

from app.core.container import CatalogServiceDep
from app.schemas.catalog import CatalogSearchParams, ExperienceCardOut, ExperienceDetailOut
from app.schemas.common import Page

router = APIRouter(prefix="/experiences", tags=["experiences"])


@router.get("", response_model=Page[ExperienceCardOut])
def search_experiences(params: Annotated[CatalogSearchParams, Query()], service: CatalogServiceDep):
    return service.search_experiences(params)


@router.get("/{experience_id}", response_model=ExperienceDetailOut)
def experience_detail(experience_id: int, service: CatalogServiceDep):
    return service.experience(experience_id)
