"""Patch-mode repair of an existing MDX draft.

Validation failures and judge revision notes route here instead of a full
regeneration — the draft is mostly fine, so we ask for a targeted fix, which
converges faster and preserves the good parts.
"""

import json
import logging

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


FIX_PROMPT = """You are an expert technical editor. Below is a complete MDX tutorial about
"{topic}" that has specific problems. Fix ONLY what the issues require — keep everything
else byte-for-byte identical.

VALIDATION ERRORS (mechanical rule violations — every one MUST be fixed):
{validation_errors}

REVIEWER REVISION NOTES (quality issues — address each one):
{revision_notes}

RULES REMINDER:
- Frontmatter block with title, description, and a non-empty tags list
- "# Introduction" heading, and a "## Summary" (or "## Conclusion") heading
- Every fenced code block has a language tag
- <Callout> type must be one of: tip, note, info, warn, danger
- <Figure> needs a non-empty alt and a src that exists in the document's current Figures
  — never invent new image URLs
- <Mermaid> needs a chart attribute; no <Video>; no raw HTML tags
- Body must be at least 500 words excluding code blocks

CURRENT MDX DOCUMENT:
{mdx_draft}

Output the complete corrected MDX file and nothing else. Do not wrap it in a code fence.
Do not add commentary.
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


async def mdx_fixer(state: AgentState) -> dict:
    topic = state.get("topic", "")
    draft = state.get("mdx_draft", "")
    errors = state.get("validation_errors", [])
    notes = state.get("revision_notes", [])
    attempts = state.get("generation_attempts", 0)

    if not draft:
        # Nothing to patch — let the validator fail it through to file_writer.
        return {"generation_attempts": attempts + 1}

    prompt = FIX_PROMPT.format(
        topic=topic,
        validation_errors=json.dumps(errors, indent=2) if errors else "(none)",
        revision_notes=json.dumps(notes, indent=2) if notes else "(none)",
        mdx_draft=draft,
    )

    try:
        llm = get_llm(temperature=0.1)
        response = await llm.ainvoke(prompt)
        fixed = _strip_code_fence_wrapper(response.content or "").strip()
    except Exception as exc:
        logger.warning("mdx_fixer failed: %s", exc)
        fixed = ""

    return {
        "mdx_draft": fixed or draft,
        "revision_notes": [],
        "generation_attempts": attempts + 1,
    }
