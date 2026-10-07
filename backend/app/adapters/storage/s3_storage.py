from typing import Any

UPLOAD_PREFIX = "uploads/"


class S3Storage:
    """Stores uploads in an S3 bucket and hands out the URLs they are publicly served from.

    The bucket makes `uploads/*` publicly readable (listing photos are public anyway); nothing else
    in it is. The server writes with its instance role, so no keys live in the app's settings.
    """

    def __init__(
        self,
        bucket: str,
        region: str,
        public_base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._bucket = bucket
        self._base = (public_base_url or f"https://{bucket}.s3.{region}.amazonaws.com").rstrip("/")
        if client is None:
            import boto3  # only needed when S3 is actually used (pip install ".[aws]")

            client = boto3.client("s3", region_name=region)
        self._client = client

    def save(self, data: bytes, name: str) -> str:
        key = f"{UPLOAD_PREFIX}{name}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType="image/webp",
            # File names are random and never reused, so browsers and CDNs may keep them forever.
            CacheControl="public, max-age=31536000, immutable",
        )
        return f"{self._base}/{key}"

    def delete(self, url: str) -> None:
        # Only uploaded files can be removed; the bundled seed images are never touched.
        prefix = f"{self._base}/{UPLOAD_PREFIX}"
        if not url.startswith(prefix):
            return
        self._client.delete_object(
            Bucket=self._bucket, Key=f"{UPLOAD_PREFIX}{url.removeprefix(prefix)}"
        )
