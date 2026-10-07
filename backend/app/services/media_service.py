import uuid

from app.domain.errors import DomainError, ErrorKind
from app.ports.storage import ImageProcessor, StorageBackend

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class MediaService:
    """Turns an uploaded image into the two stored renditions (full size and card size)."""

    def __init__(self, storage: StorageBackend, images: ImageProcessor) -> None:
        self._storage = storage
        self._images = images

    def store_image(self, data: bytes) -> tuple[str, str]:
        """Return `(url, card_url)` of the stored renditions."""
        if len(data) > MAX_UPLOAD_BYTES:
            raise DomainError(ErrorKind.BAD_REQUEST, "INVALID_IMAGE", "Images can be at most 5 MB.")
        processed = self._images.process(data)
        name = uuid.uuid4().hex
        url = self._storage.save(processed.full, f"{name}.webp")
        card_url = self._storage.save(processed.card, f"{name}_card.webp")
        return url, card_url

    def discard(self, *urls: str) -> None:
        for url in urls:
            self._storage.delete(url)
