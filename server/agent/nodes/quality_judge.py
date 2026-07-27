"""LLM-as-judge quality gate.

Runs after the structural validator passes. Scores the draft against a rubric;
one revision round through mdx_fixer if it falls below threshold. Structure can
be regex-checked — accuracy, depth, and grounding cannot.
"""

import json
import logging
import re

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)

PASS_THRESHOLD = 7.0
MAX_JUDGE_ROUNDS = 1


JUDGE_PROMPT = """You are a strict technical reviewer scoring an MDX tutorial about "{topic}".

SOURCE CONTENT the tutorial was built from (ground truth for grounding checks):
{merged_content}

TUTORIAL TO REVIEW:
{mdx_draft}

Score each dimension 1-10:
- accuracy: are the technical claims and code correct? Any bugs, wrong complexity
  claims, or misleading statements?
- depth: does it teach the topic properly — concepts, working code, pitfalls — or is
  it superficial?
- clarity: is the explanation well-ordered, plain-English first, jargon introduced
  before use?
- grounding: does it stay consistent with the source content (no invented APIs, no
  contradictions)?

Then produce revision notes: concrete, actionable edits for anything scoring below 8.
Each note must name the section and say exactly what to change.

Output JSON only, matching exactly:
{{
  "accuracy": 0,
  "depth": 0,
  "clarity": 0,
  "grounding": 0,
  "revision_notes": ["..."]
}}
"""


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_DIMENSIONS = ("accuracy", "depth", "clarity", "grounding")


def _parse_verdict(text: str) -> tuple[dict, list[str]] | None:
    match = _JSON_OBJECT_RE.search(text or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    scores: dict = {}
    for dim in _DIMENSIONS:
        try:
            scores[dim] = max(1.0, min(10.0, float(data.get(dim, 0))))
        except (TypeError, ValueError):
            return None
    notes_raw = data.get("revision_notes")
    notes = [str(n) for n in notes_raw if str(n).strip()] if isinstance(notes_raw, list) else []
    return scores, notes


async def quality_judge(state: AgentState) -> dict:
    topic = state.get("topic", "")
    draft = state.get("mdx_draft", "")
    merged = state.get("merged_content", "")
    rounds = state.get("judge_attempts", 0)

    prompt = JUDGE_PROMPT.format(
        topic=topic,
        merged_content=merged or "(empty)",
        mdx_draft=draft or "(empty)",
    )

    try:
        llm = get_llm(temperature=0.0)
        response = await llm.ainvoke(prompt)
        parsed = _parse_verdict(response.content or "")
    except Exception as exc:
        logger.warning("quality_judge failed: %s", exc)
        parsed = None

    if parsed is None:
        # Judge unavailable — don't block the pipeline, pass the draft through.
        logger.warning("quality_judge verdict unparseable; passing draft through")
        return {
            "judge_scores": {},
            "judge_overall": 0.0,
            "judge_attempts": rounds + 1,
            "revision_notes": [],
        }

    scores, notes = parsed
    overall = round(sum(scores.values()) / len(scores), 2)
    logger.info("quality_judge %r: overall=%.2f scores=%s", topic, overall, scores)

    needs_revision = overall < PASS_THRESHOLD and rounds < MAX_JUDGE_ROUNDS
    return {
        "judge_scores": scores,
        "judge_overall": overall,
        "judge_attempts": rounds + 1,
        "revision_notes": notes if needs_revision else [],
    }
