from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Stars = Annotated[int, Field(ge=1, le=5)]


class ReviewCreate(BaseModel):
    """Six category ratings; the overall rating defaults to their rounded average."""

    cleanliness: Stars
    accuracy: Stars
    check_in: Stars
    communication: Stars
    location: Stars
    value: Stars
    rating: Stars | None = None
    comment: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ReviewOut(BaseModel):
    id: int
    author_first_name: str
    author_last_initial: str
    author_avatar_url: str | None
    rating: int
    cleanliness: int
    accuracy: int
    check_in: int
    communication: int
    location: int
    value: int
    comment: str
    created_at: datetime
