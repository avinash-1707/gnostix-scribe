"""Outline-driven MDX generation.

Instead of one-shotting the whole tutorial (which truncates on long topics and
sags mid-document), sections from the outline are generated in parallel and
assembled around a deterministically-built frontmatter block.
"""

import asyncio
import json
import logging

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


COMPONENT_REFERENCE = """
============================================================
COMPONENT REFERENCE (use exactly as specified)
============================================================

CALLOUT — for tips, notes, warnings, dangers:
<Callout type="tip|note|info|warn|danger" title="Optional heading">
  Body text here. Markdown works inside.
</Callout>
Valid types: tip, note, info, warn, danger.
Use info for prerequisites and context, tip after code blocks for key insights,
warn for dangerous mistakes, note for complexity callouts, danger sparingly.

FIGURE — for provided images only:
<Figure src="<exact URL from ASSIGNED IMAGES>" alt="<descriptive alt text>" caption="<optional caption>" />
- alt is REQUIRED and must describe the image content meaningfully
- Only use src URLs from the ASSIGNED IMAGES list — never invent paths
- If ASSIGNED IMAGES is empty, do not use <Figure> at all

MERMAID — for flowcharts and diagrams:
<Mermaid chart={{`
graph TD
  A[Start] --> B[Step]
  B --> C{{Decision}}
  C -->|Yes| D[Result]
  C -->|No| E[Alternative]
`}} caption="Optional caption" />
Prefer Mermaid over Figure for anything expressible as a graph/flow.
graph TD for most cases, graph LR for pipelines.

Do not use <Video>. Use <Embed url="..." title="..." aspect="16/9" /> only when an
external reference adds significant value.

============================================================
STANDARD MARKDOWN RULES
============================================================

- ### for subsections inside this section only — never # or ## beyond the section heading
- Fenced code blocks with MANDATORY language tag (```python, ```javascript, ...)
- Inline backticks for variable/function names and keywords
- - for bullets, 1. for numbered steps, **bold** for key terms on first use only
- Standard markdown tables with a header row
- No raw HTML — use the JSX components above instead
"""


SECTION_PROMPT = """You are an expert technical writer producing ONE section of an
educational MDX tutorial about "{topic}".

FULL TUTORIAL OUTLINE (for context — other sections are written separately):
{outline_listing}

YOUR SECTION:
Heading: {heading}
Goals: {goals}
Must include a code example: {include_code}
Must include a Mermaid diagram: {include_mermaid}

SOURCE CONTENT (ground every claim in this):
{merged_content}

ASSIGNED IMAGES (JSON — embed each exactly once as a <Figure> where it fits best):
{images_json}
{component_reference}
============================================================
RULES
============================================================

- Output ONLY this section: start with the exact heading line "{heading_line}" and
  write nothing outside the section.
- Do NOT write frontmatter. Do NOT write other sections' headings or content.
- Do NOT reference other sections except by name ("see the Implementation section").
- Aim for 150-350 words of prose (code excluded).
- If this section is the Introduction: plain English, no jargon in the first paragraph,
  end with a <Callout type="info"> listing prerequisites.
- If this section is the Summary: 3-5 sentence recap, end with
  "You now understand {topic}. Next, explore [related topic]."
- If you include code: annotate complex lines with inline comments and follow tricky
  code with a <Callout type="tip"> explaining the key insight.
- Do not wrap your output in a code fence. Output raw MDX only.
"""


def _strip_code_fence_wrapper(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text
    lines = stripped.splitlines()
    if not lines:
        return text
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _build_frontmatter(outline: dict, topic: str) -> str:
    title = outline.get("title") or topic.title()
    description = outline.get("description") or f"A practical tutorial on {topic}."
    tags = outline.get("tags") or [topic.lower()]
    return (
        "---\n"
        f"title: {json.dumps(title)}\n"
        f"description: {json.dumps(description)}\n"
        f"tags: {json.dumps(tags)}\n"
        "---\n"
    )


def _assign_images(sections: list[dict], images: list[dict]) -> dict[int, list[dict]]:
    """Map each image to the section whose heading matches its placement_hint."""
    assignments: dict[int, list[dict]] = {}
    fallback_idx = next(
        (i for i, s in enumerate(sections) if s.get("level") != 1), 0
    )
    for img in images:
        hint = (img.get("placement_hint") or "").lower()
        target = fallback_idx
        for i, section in enumerate(sections):
            heading = section.get("heading", "").lower()
            if heading and (heading in hint or hint in heading) and hint:
                target = i
                break
        assignments.setdefault(target, []).append(
            {"src": img.get("src", ""), "alt": img.get("alt", ""), "caption": img.get("caption", "")}
        )
    return assignments


def _outline_listing(sections: list[dict], current_idx: int) -> str:
    lines = []
    for i, s in enumerate(sections):
        marker = "  <-- YOUR SECTION" if i == current_idx else ""
        lines.append(f"{i + 1}. {s.get('heading', '')}{marker}")
    return "\n".join(lines)


def _heading_line(section: dict) -> str:
    prefix = "#" if section.get("level") == 1 else "##"
    return f"{prefix} {section.get('heading', '')}"


async def _generate_section(
    topic: str,
    merged: str,
    sections: list[dict],
    idx: int,
    images: list[dict],
) -> str:
    section = sections[idx]
    heading_line = _heading_line(section)
    prompt = SECTION_PROMPT.format(
        topic=topic,
        outline_listing=_outline_listing(sections, idx),
        heading=section.get("heading", ""),
        goals=section.get("goals", "") or "Cover this section thoroughly.",
        include_code="yes" if section.get("include_code") else "only if it genuinely helps",
        include_mermaid="yes" if section.get("include_mermaid") else "only if a flow/graph genuinely helps",
        merged_content=merged or "(empty)",
        images_json=json.dumps(images, indent=2),
        component_reference=COMPONENT_REFERENCE,
        heading_line=heading_line,
    )
    try:
        llm = get_llm(temperature=0.3)
        response = await llm.ainvoke(prompt)
        text = _strip_code_fence_wrapper(response.content or "").strip()
    except Exception as exc:
        logger.warning("mdx_generator section %r failed: %s", section.get("heading"), exc)
        text = ""

    if text and not text.startswith(("#", heading_line)):
        text = f"{heading_line}\n\n{text}"
    return text


async def mdx_generator(state: AgentState) -> dict:
    topic = state.get("topic", "")
    merged = state.get("merged_content", "")
    outline = state.get("outline") or {}
    images = state.get("generated_images", [])
    attempts = state.get("generation_attempts", 0)

    sections = outline.get("sections") or []
    if not sections:
        logger.warning("mdx_generator: empty outline for %r", topic)
        return {"mdx_draft": "", "generation_attempts": attempts + 1}

    image_map = _assign_images(sections, images)
    section_texts = await asyncio.gather(
        *(
            _generate_section(topic, merged, sections, i, image_map.get(i, []))
            for i in range(len(sections))
        )
    )

    body = "\n\n".join(t for t in section_texts if t)
    draft = f"{_build_frontmatter(outline, topic)}\n{body}\n" if body else ""

    return {
        "mdx_draft": draft,
        "generation_attempts": attempts + 1,
    }
