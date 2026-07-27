import logging

from pydantic import BaseModel, Field

from server.agent.llm import LLMOutputError, LLMUnavailableError, invoke_json
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


class OutlineSection(BaseModel):
    heading: str
    level: int = 2
    goals: str = ""
    include_code: bool = False
    include_mermaid: bool = False


class Outline(BaseModel):
    title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    sections: list[OutlineSection] = Field(default_factory=list)


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


def _normalise(outline: Outline, topic: str) -> dict:
    sections = [
        {
            "heading": s.heading.strip(),
            "level": 1 if s.level == 1 else 2,
            "goals": s.goals.strip(),
            "include_code": s.include_code,
            "include_mermaid": s.include_mermaid,
        }
        for s in outline.sections
        if s.heading.strip()
    ]
    if not sections:
        return _default_outline(topic)
    return {
        "title": outline.title.strip() or topic.title(),
        "description": outline.description.strip() or f"A practical tutorial on {topic}.",
        "tags": [t for t in (tag.strip() for tag in outline.tags) if t] or [topic.lower()],
        "sections": sections,
    }


async def outline_planner(state: AgentState) -> dict:
    topic = state.get("topic", "")
    merged = state.get("merged_content", "")

    try:
        outline, usage = await invoke_json(
            "budget",
            OUTLINE_PROMPT.format(topic=topic, merged_content=merged or "(empty)"),
            Outline,
            temperature=0.2,
        )
    except (LLMUnavailableError, LLMOutputError) as exc:
        logger.warning("outline_planner failed, using default outline: %s", exc)
        return {
            "outline": _default_outline(topic),
            "warnings": [f"outline_planner fell back to default outline: {exc}"],
        }

    return {
        "outline": _normalise(outline, topic),
        "token_usage": {"outline_planner": usage},
    }
