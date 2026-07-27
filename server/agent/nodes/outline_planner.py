import json
import logging
import re

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


OUTLINE_PROMPT = """You are planning an educational MDX tutorial about "{topic}".

MERGED SOURCE CONTENT:
{merged_content}

Produce a JSON outline for the tutorial. Rules:
- Sections must follow this canonical order where applicable:
  Introduction (level 1), one or more Core Concept sections, Implementation / Code,
  How It Works (only if algorithmic), Time and Space Complexity (only if algorithmic),
  Common Mistakes, Summary.
- Introduction is the only level-1 heading. Everything else is level 2.
- 5 to 9 sections total.
- "goals" is 1-3 sentences describing exactly what the section must cover, grounded in
  the source content above.

Output JSON only, no commentary, matching exactly:
{{
  "title": "human-readable tutorial title",
  "description": "one-sentence frontmatter description",
  "tags": ["tag1", "tag2", "tag3"],
  "sections": [
    {{
      "heading": "Introduction",
      "level": 1,
      "goals": "what this section must cover",
      "include_code": false,
      "include_mermaid": false
    }}
  ]
}}
"""


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _default_outline(topic: str) -> dict:
    return {
        "title": topic.title(),
        "description": f"A practical tutorial on {topic}.",
        "tags": [topic.lower()],
        "sections": [
            {"heading": "Introduction", "level": 1, "goals": f"Introduce {topic}, why it matters, real-world use case, prerequisites.", "include_code": False, "include_mermaid": False},
            {"heading": "Core Concepts", "level": 2, "goals": f"Explain the core ideas behind {topic} with examples and analogies.", "include_code": False, "include_mermaid": False},
            {"heading": "Implementation", "level": 2, "goals": f"Show working, annotated code for {topic}.", "include_code": True, "include_mermaid": False},
            {"heading": "Common Mistakes", "level": 2, "goals": "List 3-5 pitfalls beginners hit.", "include_code": False, "include_mermaid": False},
            {"heading": "Summary", "level": 2, "goals": "Recap in 3-5 sentences and point to related topics.", "include_code": False, "include_mermaid": False},
        ],
    }


def _parse_outline(text: str, topic: str) -> dict:
    match = _JSON_OBJECT_RE.search(text or "")
    if not match:
        return _default_outline(topic)
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.warning("outline_planner JSON parse failed: %s", exc)
        return _default_outline(topic)

    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        return _default_outline(topic)

    clean_sections = []
    for s in sections:
        if not isinstance(s, dict) or not str(s.get("heading", "")).strip():
            continue
        clean_sections.append(
            {
                "heading": str(s["heading"]).strip(),
                "level": 1 if s.get("level") == 1 else 2,
                "goals": str(s.get("goals", "")).strip(),
                "include_code": bool(s.get("include_code")),
                "include_mermaid": bool(s.get("include_mermaid")),
            }
        )
    if not clean_sections:
        return _default_outline(topic)

    tags = data.get("tags")
    return {
        "title": str(data.get("title") or topic.title()).strip(),
        "description": str(data.get("description") or f"A practical tutorial on {topic}.").strip(),
        "tags": [str(t) for t in tags if str(t).strip()] if isinstance(tags, list) and tags else [topic.lower()],
        "sections": clean_sections,
    }


async def outline_planner(state: AgentState) -> dict:
    topic = state.get("topic", "")
    merged = state.get("merged_content", "")

    try:
        llm = get_llm("budget", temperature=0.2)
        response = await llm.ainvoke(
            OUTLINE_PROMPT.format(topic=topic, merged_content=merged or "(empty)")
        )
        outline = _parse_outline(response.content or "", topic)
    except Exception as exc:
        logger.warning("outline_planner failed: %s", exc)
        outline = _default_outline(topic)

    return {"outline": outline}
