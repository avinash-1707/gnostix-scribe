import logging

from pydantic import BaseModel, Field

from server.agent.llm import LLMOutputError, LLMUnavailableError, invoke_json
from server.agent.state import AgentState

logger = logging.getLogger(__name__)

MAX_IMAGES_PER_TOPIC = 2


ANALYSE_PROMPT = """You are reviewing educational content about "{topic}" to decide where images would genuinely help.

Content:
{merged_content}

Image generation is ALLOWED and encouraged when it adds real value. Only skip when the content + any mermaid diagrams already convey the concept fully — i.e. an extra image would be redundant.

YES (request image) — strong candidates:
- Non-trivial data structures with spatial layout (trees, graphs, linked lists, heaps, tries)
- Multi-step algorithm flows where step ordering or pointer movement matters
- System/architecture diagrams with components and arrows
- Memory layout, call stack, or other inherently spatial CS concepts
- Visual analogies or real-world illustrations that aid intuition
- Comparison/before-after visuals where a picture beats prose

SKIP only when:
- Mermaid code blocks in the content already diagram the concept clearly
- Topic is fully expressible in text/code (pure syntax notes, short definitions, trivial lists) AND no spatial/visual aspect would help
- Adding an image would just duplicate what existing diagrams or code blocks already show

Hard cap: at most 2 images per topic. Pick the highest-value ones.

Output JSON only, no commentary, matching exactly:
{{
  "images": [
    {{
      "concept": "short concept name",
      "prompt": "detailed image generation prompt — clean, minimal technical diagram, white background, clear labels, educational illustration style",
      "placement_hint": "after section heading: <exact heading text>"
    }}
  ]
}}

If no images are needed, output {{"images": []}}.
"""


class ImageRequestItem(BaseModel):
    concept: str
    prompt: str
    placement_hint: str = ""


class ImagePlan(BaseModel):
    images: list[ImageRequestItem] = Field(default_factory=list)


async def content_analyser(state: AgentState) -> dict:
    topic = state.get("topic", "")
    content = state.get("merged_content", "")
    if not content:
        return {"needs_images": False, "image_requests": []}

    try:
        plan, usage = await invoke_json(
            "budget",
            ANALYSE_PROMPT.format(topic=topic, merged_content=content),
            ImagePlan,
            temperature=0.1,
        )
    except (LLMUnavailableError, LLMOutputError) as exc:
        logger.warning("content_analyser failed: %s", exc)
        return {
            "needs_images": False,
            "image_requests": [],
            "warnings": [f"content_analyser skipped images: {exc}"],
        }

    items = [item.model_dump() for item in plan.images[:MAX_IMAGES_PER_TOPIC]]
    return {
        "needs_images": bool(items),
        "image_requests": items,
        "token_usage": {"content_analyser": usage},
    }
