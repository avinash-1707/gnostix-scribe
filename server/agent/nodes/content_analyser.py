import json
import logging
import re

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


ANALYSE_PROMPT = """You are reviewing educational content about "{topic}" to decide where images would help.

Content:
{merged_content}

Rules for deciding when an image is needed:
- Data structures (trees, graphs, linked lists, stacks, queues) -> YES, always
- Algorithm flows / step-by-step processes -> YES
- System architecture or network diagrams -> YES
- Abstract CS concepts with spatial structure (memory layout, recursion call stack) -> YES
- Simple syntax or API usage (e.g. string methods, file I/O) -> NO
- Pure text definitions -> NO

For each concept that needs an image, output a JSON array:
[
  {{
    "concept": "short concept name",
    "prompt": "detailed image generation prompt for Gemini — describe a clean, minimal technical diagram with white background, labelled clearly, educational illustration style",
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

    return {
        "needs_images": bool(items),
        "image_requests": items,
    }
