from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    full: bytes  # 1440px wide, WebP
    card: bytes  # 720px wide, WebP


class StorageBackend(Protocol):
    def save(self, data: bytes, name: str) -> str:
        """Store `data` and return the public URL it is served from."""

    def delete(self, url: str) -> None:
        """Remove a stored file. Unknown or non-uploaded URLs are ignored."""


class ImageProcessor(Protocol):
    def process(self, data: bytes) -> ProcessedImage:
        """Raise DomainError(BAD_REQUEST, "INVALID_IMAGE") unless `data` is a JPEG, PNG or
        WebP image."""
