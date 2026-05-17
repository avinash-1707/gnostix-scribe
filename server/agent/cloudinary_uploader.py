import asyncio

import cloudinary
import cloudinary.uploader

from server.config import settings


_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL, secure=True)
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
