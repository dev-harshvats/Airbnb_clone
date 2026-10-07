from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, EmailStr, Field, field_validator

from app.domain.auth_policy import normalize_email, password_problem
from app.schemas.user import Name, UserOut

Email = Annotated[
    EmailStr,
    BeforeValidator(lambda v: v.strip() if isinstance(v, str) else v),
    AfterValidator(normalize_email),
]


class CheckEmailRequest(BaseModel):
    email: Email


class CheckEmailResponse(BaseModel):
    exists: bool


class SignupRequest(BaseModel):
    email: Email
    password: str
    first_name: Name
    last_name: Name
    date_of_birth: date = Field(ge=date(1900, 1, 1))  # future dates fail the age rule (UNDER_AGE)

    @field_validator("password")
    @classmethod
    def _strong_password(cls, value: str) -> str:
        problem = password_problem(value)
        if problem:
            raise ValueError(problem)
        return value


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=256)


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # seconds until the access token expires
    user: UserOut
