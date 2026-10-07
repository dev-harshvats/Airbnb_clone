from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.sql.models import UserModel
from app.domain.entities import NewUser, User
from app.domain.errors import DomainError, ErrorKind


def to_user(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        first_name=row.first_name,
        last_name=row.last_name,
        date_of_birth=row.date_of_birth,
        avatar_url=row.avatar_url,
        bio=row.bio,
        is_host=row.is_host,
        is_superhost=row.is_superhost,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: int) -> User | None:
        row = self._session.get(UserModel, user_id)
        return to_user(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return to_user(row) if row else None

    def add(self, new: NewUser) -> User:
        row = UserModel(**asdict(new))
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise DomainError(
                ErrorKind.CONFLICT, "EMAIL_TAKEN", "That email is already registered."
            ) from exc
        return to_user(row)

    def update(self, user: User) -> User:
        row = self._session.get(UserModel, user.id)
        if row is None:
            raise DomainError(ErrorKind.NOT_FOUND, "USER_NOT_FOUND", "User not found.")
        for field, value in asdict(user).items():
            if field != "id":
                setattr(row, field, value)
        self._session.flush()
        return to_user(row)
