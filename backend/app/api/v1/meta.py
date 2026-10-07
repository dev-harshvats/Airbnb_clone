from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.core.container import SearchServiceDep
from app.schemas.listing import AmenityOut, CategoryOut, DestinationOut, LocationSuggestion

router = APIRouter(tags=["meta"])

_CACHE_ONE_HOUR = "public, max-age=3600"  # reference data that rarely changes


@router.get("/categories", response_model=list[CategoryOut])
def categories(response: Response, service: SearchServiceDep):
    response.headers["Cache-Control"] = _CACHE_ONE_HOUR
    return service.categories()


@router.get("/amenities", response_model=list[AmenityOut])
def amenities(response: Response, service: SearchServiceDep):
    response.headers["Cache-Control"] = _CACHE_ONE_HOUR
    return service.amenities()


@router.get("/locations/suggest", response_model=list[LocationSuggestion])
def suggest_locations(service: SearchServiceDep, q: Annotated[str, Query(max_length=100)] = ""):
    return service.suggest_locations(q)


@router.get("/destinations", response_model=list[DestinationOut])
def destinations(response: Response, service: SearchServiceDep):
    response.headers["Cache-Control"] = "public, max-age=300"
    return service.destinations()
