import logging
import re

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


MERGE_PROMPT = """You are a content editor. You have three sources of content about "{topic}":

SOURCE 1 — GeeksForGeeks (primary, authoritative):
{gfg_raw}

SOURCE 2 — TpointTech (secondary, supplementary):
{tpointtech_raw}

SOURCE 3 — Internal knowledge (gaps + analogies only):
{llm_knowledge_raw}

SOURCE 4 — Gap-fill content written after a failed coverage check (use to fill whatever
the other sources miss; may be empty on the first pass):
{gap_content}

Your task:
1. Identify the major sections/concepts this topic requires for a complete tutorial.
2. For each section, select the best content from the available sources (prioritise Source 1).
3. If Source 1 has a gap for a section, use Source 2. If both are missing it, use Source 3
   and Source 4.
4. Remove duplicate explanations — keep only the clearest version.
5. Preserve all code examples exactly as scraped (do not paraphrase code).
6. Output a single structured document with clear section headings.
   This document will be used to generate an MDX tutorial — so make it thorough.

Output the merged content only. No commentary.
"""


_HEADING_RE = re.compile(r"(?m)^#{1,6} .+")
_CODE_FENCE_RE = re.compile(r"```")
_CODE_INDENT_RE = re.compile(r"(?m)^    \S")


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _meets_coverage(text: str) -> bool:
    words = _word_count(text)
    sections = len(_HEADING_RE.findall(text))
    has_code = bool(_CODE_FENCE_RE.search(text) or _CODE_INDENT_RE.search(text))
    return words >= 400 and sections >= 2 and has_code


async def content_merger(state: AgentState) -> dict:
    topic = state.get("topic", "")
    attempts = state.get("scrape_attempts", 0)

    prompt = MERGE_PROMPT.format(
        topic=topic,
        gfg_raw=state.get("gfg_raw") or "(empty)",
        tpointtech_raw=state.get("tpointtech_raw") or "(empty)",
        llm_knowledge_raw=state.get("llm_knowledge_raw") or "(empty)",
        gap_content=state.get("gap_content") or "(empty)",
    )

    try:
        llm = get_llm("writer", temperature=0.2)
        response = await llm.ainvoke(prompt)
        merged = response.content or ""
    except Exception as exc:
        logger.warning("content_merger LLM call failed: %s", exc)
        merged = state.get("merged_content", "")

    return {
        "merged_content": merged,
        "coverage_ok": _meets_coverage(merged),
        "scrape_attempts": attempts + 1,
    }
