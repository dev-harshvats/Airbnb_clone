from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bookings,
    experiences,
    health,
    hosting,
    listings,
    meta,
    services,
    users,
    wishlists,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(meta.router)
api_router.include_router(listings.router)
api_router.include_router(bookings.router)
api_router.include_router(wishlists.router)
api_router.include_router(hosting.router)
api_router.include_router(experiences.router)
api_router.include_router(services.router)
