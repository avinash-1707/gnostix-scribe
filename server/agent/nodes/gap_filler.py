import logging
import re

from server.agent.llm import LLMUnavailableError, invoke_text
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


GAP_PROMPT = """You are a technical educator. A tutorial document about "{topic}" failed a
coverage check — it must have at least 400 words, 2 sections, and 1 code example, and it
is missing some of that.

CURRENT MERGED DOCUMENT:
{merged_content}

Your task:
1. List the essential sections a complete tutorial on this topic needs but the document
   lacks (or covers too thinly).
2. Write that missing content yourself: full prose explanations, and runnable code
   examples in fenced code blocks with language tags where the topic calls for them.

Output only the new supplementary content, structured with markdown ## headings.
Do not repeat content the document already covers. No commentary.
"""


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


async def gap_filler(state: AgentState) -> dict:
    topic = state.get("topic", "")
    merged = state.get("merged_content", "")

    try:
        gap, usage = await invoke_text(
            "budget",
            GAP_PROMPT.format(topic=topic, merged_content=merged or "(empty)"),
            temperature=0.4,
        )
    except LLMUnavailableError as exc:
        logger.warning("gap_filler failed: %s", exc)
        return {"gap_content": "", "warnings": [f"gap_filler unavailable: {exc}"]}

    logger.info("gap_filler produced %d words for %r", _word_count(gap), topic)
    return {"gap_content": gap, "token_usage": {"gap_filler": usage}}
