import io

from PIL import Image, ImageOps, UnidentifiedImageError

from app.domain.errors import DomainError, ErrorKind
from app.ports.storage import ProcessedImage

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
FULL_WIDTH = 1440
CARD_WIDTH = 720
WEBP_QUALITY = 80


class PillowImageProcessor:
    def process(self, data: bytes) -> ProcessedImage:
        try:
            image = Image.open(io.BytesIO(data))
            if image.format not in ALLOWED_FORMATS:
                raise ValueError(image.format)
            image = ImageOps.exif_transpose(image).convert("RGB")
        except (UnidentifiedImageError, ValueError, OSError) as exc:
            raise DomainError(
                ErrorKind.BAD_REQUEST, "INVALID_IMAGE", "Upload a JPEG, PNG or WebP image."
            ) from exc
        return ProcessedImage(
            full=self._render(image, FULL_WIDTH), card=self._render(image, CARD_WIDTH)
        )

    @staticmethod
    def _render(image: Image.Image, width: int) -> bytes:
        resized = image.copy()
        if resized.width > width:  # never upscale
            resized = resized.resize((width, round(resized.height * width / resized.width)))
        out = io.BytesIO()
        resized.save(out, format="WEBP", quality=WEBP_QUALITY)
        return out.getvalue()
