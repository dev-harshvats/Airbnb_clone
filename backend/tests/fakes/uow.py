"""In-memory implementations of the persistence ports, used for fast service tests
and as the second implementation in the port contract tests (Liskov)."""

import copy
from dataclasses import asdict, replace
from datetime import datetime

from app.domain.booking_policy import overlaps
from app.domain.entities import Booking, NewBooking, NewRefreshToken, NewUser, RefreshToken, User
from app.domain.enums import BookingStatus
from app.domain.errors import DomainError, ErrorKind


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.rows: dict[int, User] = {}
        self._next_id = 1

    def get_by_id(self, user_id: int) -> User | None:
        return self.rows.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    def add(self, new: NewUser) -> User:
        if self.get_by_email(new.email) is not None:
            raise DomainError(ErrorKind.CONFLICT, "EMAIL_TAKEN", "Email already registered.")
        user = User(id=self._next_id, **asdict(new))
        self._next_id += 1
        self.rows[user.id] = user
        return user

    def update(self, user: User) -> User:
        self.rows[user.id] = user
        return user


class InMemoryRefreshTokenStore:
    def __init__(self) -> None:
        self.rows: dict[int, RefreshToken] = {}
        self._next_id = 1

    def add(self, new: NewRefreshToken) -> RefreshToken:
        token = RefreshToken(id=self._next_id, revoked_at=None, replaced_by_id=None, **asdict(new))
        self._next_id += 1
        self.rows[token.id] = token
        return token

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self.rows.values() if t.token_hash == token_hash), None)

    def revoke(self, token_id: int, when: datetime, replaced_by_id: int | None = None) -> None:
        self.rows[token_id] = replace(
            self.rows[token_id], revoked_at=when, replaced_by_id=replaced_by_id
        )

    def revoke_family(self, family_id: str, when: datetime) -> int:
        count = 0
        for token_id, token in list(self.rows.items()):
            if token.family_id == family_id and token.revoked_at is None:
                self.rows[token_id] = replace(token, revoked_at=when)
                count += 1
        return count

    def purge_expired(self, before: datetime) -> int:
        expired = [token_id for token_id, token in self.rows.items() if token.expires_at < before]
        for token_id in expired:
            del self.rows[token_id]
        return len(expired)


class InMemoryBookingRepository:
    def __init__(self) -> None:
        self.rows: dict[int, Booking] = {}
        self._next_id = 1

    def add(self, new: NewBooking) -> Booking:
        booking = Booking(
            id=self._next_id, status=BookingStatus.CONFIRMED, cancelled_at=None, **asdict(new)
        )
        self._next_id += 1
        self.rows[booking.id] = booking
        return booking

    def get_by_code(self, code: str) -> Booking | None:
        return next((b for b in self.rows.values() if b.code == code), None)

    def get_by_idempotency_key(self, guest_id: int, key: str) -> Booking | None:
        return next(
            (b for b in self.rows.values() if b.guest_id == guest_id and b.idempotency_key == key),
            None,
        )

    def _confirmed(self, listing_id: int):
        return [
            b
            for b in self.rows.values()
            if b.listing_id == listing_id and b.status == BookingStatus.CONFIRMED
        ]

    def has_overlap(self, listing_id: int, check_in, check_out) -> bool:
        return any(
            overlaps(b.check_in, b.check_out, check_in, check_out)
            for b in self._confirmed(listing_id)
        )

    def booked_ranges(self, listing_id: int, start, end):
        stays = [
            b for b in self._confirmed(listing_id) if overlaps(b.check_in, b.check_out, start, end)
        ]
        return sorted((b.check_in, b.check_out) for b in stays)

    def mark_cancelled(self, booking_id: int, when: datetime) -> Booking:
        self.rows[booking_id] = replace(
            self.rows[booking_id], status=BookingStatus.CANCELLED, cancelled_at=when
        )
        return self.rows[booking_id]

    def list_for_guest(self, guest_id: int) -> list[Booking]:
        mine = [b for b in self.rows.values() if b.guest_id == guest_id]
        return sorted(mine, key=lambda b: (b.check_in, b.id), reverse=True)


class InMemoryUnitOfWork:
    """Models commit/rollback: only committed state survives `discard_uncommitted()`."""

    def __init__(self) -> None:
        self.users = InMemoryUserRepository()
        self.refresh_tokens = InMemoryRefreshTokenStore()
        self.bookings = InMemoryBookingRepository()
        self.commits = 0
        self._snapshot = self._state()

    def _state(self):
        return copy.deepcopy(
            (
                self.users.rows,
                self.users._next_id,
                self.refresh_tokens.rows,
                self.refresh_tokens._next_id,
                self.bookings.rows,
                self.bookings._next_id,
            )
        )

    def commit(self) -> None:
        self.commits += 1
        self._snapshot = self._state()

    def rollback(self) -> None:
        self.discard_uncommitted()

    def discard_uncommitted(self) -> None:
        users, user_id, tokens, token_id, bookings, booking_id = copy.deepcopy(self._snapshot)
        self.users.rows, self.users._next_id = users, user_id
        self.refresh_tokens.rows, self.refresh_tokens._next_id = tokens, token_id
        self.bookings.rows, self.bookings._next_id = bookings, booking_id
