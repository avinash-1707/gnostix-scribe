import asyncio
import base64
import logging

from google import genai
from openai import OpenAI

from server.agent.cloudinary_uploader import upload_png_bytes
from server.agent.slugify import slugify
from server.agent.state import AgentState
from server.config import settings

logger = logging.getLogger(__name__)


GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
OPENAI_IMAGE_MODEL = "gpt-image-1"
MAX_IMAGES_PER_TOPIC = 2


_gemini_client: genai.Client | None = None
_openai_client: OpenAI | None = None


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


def _generate_png(prompt: str) -> bytes | None:
    data = _generate_png_gemini(prompt)
    if data:
        return data
    logger.info("falling back to openai for image generation")
    return _generate_png_openai(prompt)


async def image_generator(state: AgentState) -> dict:
    topic_slug = state.get("topic_slug") or slugify(state.get("topic", "topic"))
    results: list[dict] = []

    requests = state.get("image_requests", [])[:MAX_IMAGES_PER_TOPIC]

    for item in requests:
        concept = item.get("concept", "concept")
        prompt = item.get("prompt", "")
        if not prompt:
            continue
        data = await asyncio.to_thread(_generate_png, prompt)
        if not data:
            logger.warning("skipping image for concept '%s' (no bytes from any provider)", concept)
            continue
        concept_slug = slugify(concept) or "concept"
        public_id = f"mdx-agent/{topic_slug}/{concept_slug}"
        try:
            url = await upload_png_bytes(data, public_id)
        except Exception as exc:
            logger.warning("cloudinary upload failed for '%s': %s", concept, exc)
            continue
        results.append(
            {
                "src": url,
                "alt": concept,
                "caption": concept,
                "placement_hint": item.get("placement_hint", ""),
            }
        )

    return {"generated_images": results}
