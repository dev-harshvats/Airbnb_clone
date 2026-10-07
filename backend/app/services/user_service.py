from dataclasses import replace

from app.domain.entities import User
from app.domain.errors import DomainError, ErrorKind
from app.ports.clock import Clock
from app.ports.uow import UnitOfWork

PROFILE_FIELDS = frozenset({"first_name", "last_name", "bio", "avatar_url"})


class UserService:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def update_profile(self, user: User, changes: dict) -> User:
        unknown = set(changes) - PROFILE_FIELDS
        if unknown:  # defence in depth: the schema already forbids these
            raise DomainError(
                ErrorKind.BAD_REQUEST, "FIELD_NOT_EDITABLE", f"Cannot edit: {sorted(unknown)}"
            )
        updated = self._uow.users.update(replace(user, **changes, updated_at=self._clock.now()))
        self._uow.commit()
        return updated

    def become_host(self, user: User) -> User:
        if user.is_host:
            return user
        updated = self._uow.users.update(replace(user, is_host=True, updated_at=self._clock.now()))
        self._uow.commit()
        return updated

    def get_host_profile(self, user_id: int) -> User:
        """A public profile exists only for hosts; everyone else is reported as not found so
        the endpoint cannot be used to enumerate guest accounts."""
        user = self._uow.users.get_by_id(user_id)
        if user is None or not user.is_host:
            raise DomainError(ErrorKind.NOT_FOUND, "USER_NOT_FOUND", "Host not found.")
        return user
