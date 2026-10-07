from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.adapters.sql.booking_repo import SqlBookingRepository
from app.adapters.sql.catalog_reader import SqlExperienceReader, SqlServiceReader
from app.adapters.sql.host_reader import SqlHostReader
from app.adapters.sql.listing_reader import SqlListingReader
from app.adapters.sql.listing_repo import SqlListingRepository
from app.adapters.sql.refresh_token_store import SqlRefreshTokenStore
from app.adapters.sql.review_repo import SqlReviewRepository
from app.adapters.sql.user_repo import SqlUserRepository
from app.adapters.sql.wishlist_repo import SqlWishlistRepository


class SqlUnitOfWork:
    """Wraps one SQLAlchemy session (one per request). The session itself is opened and closed
    by the `get_db` dependency; closing it without a commit discards uncommitted work."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self.users = SqlUserRepository(session)
        self.refresh_tokens = SqlRefreshTokenStore(session)
        self.listings = SqlListingRepository(session)
        self.listing_reader = SqlListingReader(session)
        self.host_reader = SqlHostReader(session)
        self.bookings = SqlBookingRepository(session)
        self.reviews = SqlReviewRepository(session)
        self.wishlists = SqlWishlistRepository(session)
        self.experience_reader = SqlExperienceReader(session)
        self.service_reader = SqlServiceReader(session)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    @contextmanager
    def write(self) -> Iterator[None]:
        """SQLite: BEGIN IMMEDIATE takes the single write lock up front (other writers wait up to
        the busy timeout), so what we read next cannot change before we write."""
        self._session.execute(text("BEGIN IMMEDIATE"))
        try:
            yield
        except BaseException:
            self._session.rollback()
            raise
