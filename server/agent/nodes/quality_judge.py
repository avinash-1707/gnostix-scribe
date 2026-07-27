"""LLM-as-judge quality gate.

Runs after the structural validator passes. Scores the draft against a rubric;
one revision round through mdx_fixer if it falls below threshold. Structure can
be regex-checked — accuracy, depth, and grounding cannot.
"""

import logging

from pydantic import BaseModel, Field

from server.agent.llm import LLMOutputError, LLMUnavailableError, invoke_json
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


class JudgeVerdict(BaseModel):
    accuracy: float
    depth: float
    clarity: float
    grounding: float
    revision_notes: list[str] = Field(default_factory=list)


_DIMENSIONS = ("accuracy", "depth", "clarity", "grounding")


def _clamp(value: float) -> float:
    return max(1.0, min(10.0, float(value)))


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
        verdict, usage = await invoke_json("judge", prompt, JudgeVerdict, temperature=0.0)
    except (LLMUnavailableError, LLMOutputError) as exc:
        # Judge unavailable — don't block the pipeline, pass the draft through.
        logger.warning("quality_judge unavailable; passing draft through: %s", exc)
        return {
            "judge_scores": {},
            "judge_overall": 0.0,
            "judge_attempts": rounds + 1,
            "revision_notes": [],
            "warnings": [f"quality_judge skipped: {exc}"],
        }

    scores = {dim: _clamp(getattr(verdict, dim)) for dim in _DIMENSIONS}
    overall = round(sum(scores.values()) / len(scores), 2)
    notes = [n for n in verdict.revision_notes if n.strip()]
    logger.info("quality_judge %r: overall=%.2f scores=%s", topic, overall, scores)

    needs_revision = overall < PASS_THRESHOLD and rounds < MAX_JUDGE_ROUNDS
    return {
        "judge_scores": scores,
        "judge_overall": overall,
        "judge_attempts": rounds + 1,
        "revision_notes": notes if needs_revision else [],
        "token_usage": {"quality_judge": usage},
    }
