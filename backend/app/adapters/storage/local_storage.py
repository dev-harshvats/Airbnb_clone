from pathlib import Path

UPLOAD_URL_PREFIX = "/media/uploads/"


class LocalStorage:
    """Stores uploads on local disk under MEDIA_DIR/uploads and serves them from /media."""

    def __init__(self, media_dir: Path) -> None:
        self._dir = Path(media_dir) / "uploads"
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, name: str) -> str:
        (self._dir / name).write_bytes(data)
        return f"{UPLOAD_URL_PREFIX}{name}"

    def delete(self, url: str) -> None:
        # Only uploaded files can be removed; the bundled seed images are never touched.
        if not url.startswith(UPLOAD_URL_PREFIX):
            return
        (self._dir / url.removeprefix(UPLOAD_URL_PREFIX)).unlink(missing_ok=True)
