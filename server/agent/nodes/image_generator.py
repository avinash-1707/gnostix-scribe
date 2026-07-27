"""Image generation node.

Primary path: OpenRouter chat completions with ``modalities: ["image","text"]``
— default model google/gemini-2.5-flash-image (~$0.04/image at 1K), with
google/gemini-3.1-flash-lite-image as an automatic cross-model fallback.
Images come back as base64 data URLs in ``message.images[]``.

Legacy path (no OPENROUTER_API_KEY): direct Gemini via google-genai, then
OpenAI gpt-image-1. All requests for a topic run in parallel; each result is
uploaded to Cloudinary and its secure_url embedded downstream.
"""

import asyncio
import base64
import logging

from google import genai
from openai import AsyncOpenAI, OpenAI

from server.agent.cloudinary_uploader import upload_png_bytes
from server.agent.slugify import slugify
from server.agent.state import AgentState
from server.config import settings

logger = logging.getLogger(__name__)


OPENROUTER_IMAGE_MODEL = "google/gemini-2.5-flash-image"
OPENROUTER_IMAGE_FALLBACKS = ["google/gemini-3.1-flash-lite-image"]
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
OPENAI_IMAGE_MODEL = "gpt-image-1"
MAX_IMAGES_PER_TOPIC = 2
_ATTEMPTS = 2
_CALL_TIMEOUT_S = 120.0


_openrouter_client: AsyncOpenAI | None = None
_gemini_client: genai.Client | None = None
_openai_client: OpenAI | None = None


def _get_openrouter_client() -> AsyncOpenAI | None:
    global _openrouter_client
    if not settings.OPENROUTER_API_KEY:
        return None
    if _openrouter_client is None:
        _openrouter_client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": settings.CLIENT_URL,
                "X-Title": "gnostix-scribe",
            },
        )
    return _openrouter_client


def _get_gemini_client() -> genai.Client | None:
    global _gemini_client
    if not settings.GOOGLE_API_KEY:
        return None
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    return _gemini_client


def _get_openai_client() -> OpenAI | None:
    global _openai_client
    if not settings.OPENAI_API_KEY:
        return None
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _decode_image_entry(entry) -> bytes | None:
    """Defensively extract image bytes from one message.images[] entry.

    Canonical shape is {"type": "image_url", "image_url": {"url": "data:..."}}
    but some providers return {url}/{b64_json}/{data} variants.
    """
    if not isinstance(entry, dict):
        entry = getattr(entry, "model_dump", lambda: {})() or {}
    image_url = entry.get("image_url")
    url = ""
    if isinstance(image_url, dict):
        url = image_url.get("url") or ""
    if not url:
        url = entry.get("url") or ""
    b64 = entry.get("b64_json") or entry.get("data") or ""
    if url.startswith("data:"):
        try:
            b64 = url.split(",", 1)[1]
        except IndexError:
            return None
    if not b64:
        return None
    try:
        return base64.b64decode(b64)
    except Exception:
        return None


async def _generate_png_openrouter(prompt: str) -> bytes | None:
    client = _get_openrouter_client()
    if client is None:
        return None
    model = settings.OPENROUTER_MODEL_IMAGE or OPENROUTER_IMAGE_MODEL
    fallbacks = [m for m in OPENROUTER_IMAGE_FALLBACKS if m != model]
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                extra_body={
                    "modalities": ["image", "text"],
                    "image_config": {"aspect_ratio": "4:3", "image_size": "1K"},
                    "models": fallbacks,
                },
            ),
            timeout=_CALL_TIMEOUT_S,
        )
    except Exception as exc:
        logger.warning("openrouter image generation failed: %s", exc)
        return None

    message = response.choices[0].message if response.choices else None
    images = getattr(message, "images", None) or []
    for entry in images:
        data = _decode_image_entry(entry)
        if data:
            logger.info("openrouter image generation succeeded (%d bytes)", len(data))
            return data
    logger.warning("openrouter image generation returned no image bytes")
    return None


def _extract_gemini_image_bytes(response) -> bytes | None:
    candidates = getattr(response, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                mime = getattr(inline, "mime_type", "") or ""
                if mime.startswith("image/"):
                    return inline.data
    return None


def _generate_png_gemini(prompt: str) -> bytes | None:
    client = _get_gemini_client()
    if client is None:
        return None
    try:
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=prompt,
        )
        data = _extract_gemini_image_bytes(response)
        if data:
            logger.info("gemini image generation succeeded (%d bytes)", len(data))
        else:
            logger.warning("gemini image generation returned no image bytes")
        return data
    except Exception as exc:
        logger.warning("gemini image generation failed: %s", exc)
        return None


def _generate_png_openai(prompt: str) -> bytes | None:
    client = _get_openai_client()
    if client is None:
        return None
    try:
        response = client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        data = response.data[0] if response.data else None
        b64 = getattr(data, "b64_json", None) if data else None
        if not b64:
            logger.warning("openai image generation returned no image bytes")
            return None
        png = base64.b64decode(b64)
        logger.info("openai image generation succeeded (%d bytes)", len(png))
        return png
    except Exception as exc:
        logger.warning("openai image generation failed: %s", exc)
        return None


async def _generate_png(prompt: str) -> bytes | None:
    if settings.OPENROUTER_API_KEY:
        for attempt in range(_ATTEMPTS):
            data = await _generate_png_openrouter(prompt)
            if data:
                return data
            if attempt + 1 < _ATTEMPTS:
                await asyncio.sleep(2.0)
        return None
    # Legacy path: direct Gemini, then OpenAI images.
    data = await asyncio.to_thread(_generate_png_gemini, prompt)
    if data:
        return data
    logger.info("falling back to openai for image generation")
    return await asyncio.to_thread(_generate_png_openai, prompt)


async def _generate_and_upload(topic_slug: str, item: dict) -> dict | None:
    concept = item.get("concept", "concept")
    prompt = item.get("prompt", "")
    if not prompt:
        return None
    data = await _generate_png(prompt)
    if not data:
        logger.warning("skipping image for concept '%s' (no bytes from any provider)", concept)
        return None
    concept_slug = slugify(concept) or "concept"
    public_id = f"mdx-agent/{topic_slug}/{concept_slug}"
    try:
        url = await upload_png_bytes(data, public_id)
    except Exception as exc:
        logger.warning("cloudinary upload failed for '%s': %s", concept, exc)
        return None
    return {
        "src": url,
        "alt": concept,
        "caption": concept,
        "placement_hint": item.get("placement_hint", ""),
    }


async def image_generator(state: AgentState) -> dict:
    topic_slug = state.get("topic_slug") or slugify(state.get("topic", "topic"))
    requests = state.get("image_requests", [])[:MAX_IMAGES_PER_TOPIC]

    results = await asyncio.gather(
        *(_generate_and_upload(topic_slug, item) for item in requests)
    )
    images = [r for r in results if r]

    output: dict = {"generated_images": images}
    if len(images) < len(requests):
        output["warnings"] = [
            f"image_generator: {len(requests) - len(images)}/{len(requests)} images failed"
        ]
    return output
