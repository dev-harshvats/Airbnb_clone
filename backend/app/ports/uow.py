from contextlib import AbstractContextManager
from typing import Protocol

from app.ports.repositories import (
    BookingRepository,
    ExperienceReader,
    HostReader,
    ListingReader,
    ListingRepository,
    RefreshTokenStore,
    ReviewRepository,
    ServiceReader,
    UserRepository,
    WishlistRepository,
)


class UnitOfWork(Protocol):
    """One request's view of persistence. Nothing is durable until `commit()`."""

    users: UserRepository
    refresh_tokens: RefreshTokenStore
    listings: ListingRepository
    listing_reader: ListingReader
    host_reader: HostReader
    bookings: BookingRepository
    reviews: ReviewRepository
    wishlists: WishlistRepository
    experience_reader: ExperienceReader
    service_reader: ServiceReader

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def write(self) -> AbstractContextManager[None]:
        """Take the database's exclusive write lock for the rest of this transaction, so a
        check-then-insert (such as "is it free? then book it") cannot interleave with another
        request. Leaving the block with an exception rolls the transaction back."""
