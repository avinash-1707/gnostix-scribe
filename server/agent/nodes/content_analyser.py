import json
import logging
import re

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


ANALYSE_PROMPT = """You are reviewing educational content about "{topic}" to decide where images would genuinely help.

Content:
{merged_content}

Default to NO image. Only emit a request when a diagram is strictly necessary to understand the concept — text alone would leave the reader confused.

YES (image required):
- Non-trivial data structures with spatial layout (trees, graphs, linked lists, heaps, tries)
- Multi-step algorithm flows where step ordering or pointer movement matters
- System/architecture diagrams with components and arrows
- Memory layout, call stack, or other inherently spatial CS concepts

NO (skip image):
- Syntax, API usage, language features, string/file/IO operations
- Pure text definitions, history, comparisons, lists of features
- Topics already clear from the code blocks in the content
- Anything a competent reader understands without a picture

Hard cap: at most 2 images per topic. Pick only the highest-value ones. If unsure, output [].

For each concept that truly needs an image, output a JSON array (max 2 items):
[
  {{
    "concept": "short concept name",
    "prompt": "detailed image generation prompt — clean, minimal technical diagram, white background, clear labels, educational illustration style",
    "placement_hint": "after section heading: <exact heading text>"
  }}
]

If no images are needed, output an empty array: []
Output JSON only. No commentary.
"""


_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def _parse_json_array(text: str) -> list[dict]:
    if not text:
        return []
    match = _JSON_ARRAY_RE.search(text)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.warning("content_analyser JSON parse failed: %s", exc)
        return []
    if not isinstance(data, list):
        return []
    out: list[dict] = []
    for item in data:
        if isinstance(item, dict) and item.get("concept") and item.get("prompt"):
            out.append(
                {
                    "concept": str(item["concept"]),
                    "prompt": str(item["prompt"]),
                    "placement_hint": str(item.get("placement_hint", "")),
                }
            )
    return out


async def content_analyser(state: AgentState) -> dict:
    topic = state.get("topic", "")
    content = state.get("merged_content", "")
    if not content:
        return {"needs_images": False, "image_requests": []}

    try:
        llm = get_llm(temperature=0.1)
        response = await llm.ainvoke(
            ANALYSE_PROMPT.format(topic=topic, merged_content=content)
        )
        items = _parse_json_array(response.content or "")
    except Exception as exc:
        logger.warning("content_analyser failed: %s", exc)
        items = []

    items = items[:2]

    return {
        "needs_images": bool(items),
        "image_requests": items,
    }
