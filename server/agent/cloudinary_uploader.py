import asyncio
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader

from server.config import settings


_configured = False


def _parse_cloudinary_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "cloudinary":
        raise ValueError(f"invalid CLOUDINARY_URL scheme: {parsed.scheme!r}")
    if not parsed.username or not parsed.password or not parsed.hostname:
        raise ValueError("CLOUDINARY_URL missing api_key, api_secret, or cloud_name")
    return {
        "api_key": parsed.username,
        "api_secret": parsed.password,
        "cloud_name": parsed.hostname,
    }


def _configure() -> None:
    global _configured
    if _configured:
        return
    if not settings.CLOUDINARY_URL:
        raise RuntimeError("CLOUDINARY_URL not set")
    creds = _parse_cloudinary_url(settings.CLOUDINARY_URL)
    cloudinary.config(secure=True, **creds)
    _configured = True


async def upload_png_bytes(data: bytes, public_id: str) -> str:
    _configure()
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        data,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
    return result["secure_url"]
