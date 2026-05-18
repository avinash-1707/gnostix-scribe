import asyncio
import logging

from google import genai

from server.agent.cloudinary_uploader import upload_png_bytes
from server.agent.slugify import slugify
from server.agent.state import AgentState
from server.config import settings

logger = logging.getLogger(__name__)


IMAGE_MODEL = "gemini-2.5-flash-image"


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    return _client


def _extract_image_bytes(response) -> bytes | None:
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


def _generate_png(prompt: str) -> bytes | None:
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
        )
        return _extract_image_bytes(response)
    except Exception as exc:
        logger.warning("image generation failed: %s", exc)
        return None


async def image_generator(state: AgentState) -> dict:
    topic_slug = state.get("topic_slug") or slugify(state.get("topic", "topic"))
    results: list[dict] = []

    for item in state.get("image_requests", []):
        concept = item.get("concept", "concept")
        prompt = item.get("prompt", "")
        if not prompt:
            continue
        data = await asyncio.to_thread(_generate_png, prompt)
        if not data:
            logger.warning("skipping image for concept '%s' (no bytes returned)", concept)
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
