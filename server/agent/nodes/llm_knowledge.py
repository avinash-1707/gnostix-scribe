import logging

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


PROMPT = """You are a technical educator writing supplementary content for the topic: "{topic}".

A web scraper has already pulled raw article content from GeeksForGeeks and TpointTech.
Your job is NOT to repeat what those sites cover — your job is to add what they typically miss:

1. A plain-English intuitive explanation of the core concept (no jargon first)
2. A real-world analogy that makes the concept click
3. Common misconceptions beginners have about this topic
4. Any prerequisite concepts a learner should understand before tackling this topic
5. Connections to related topics in the same domain

Keep each section concise (3-5 sentences max). Use clear, simple language.
Do not write code — that will come from the scraped sources.
Output as structured plain text with labelled sections.
"""


async def llm_knowledge(state: AgentState) -> dict:
    topic = state.get("topic", "")
    if not topic:
        return {"llm_knowledge_raw": ""}
    try:
        llm = get_llm("budget", temperature=0.4)
        response = await llm.ainvoke(PROMPT.format(topic=topic))
        return {"llm_knowledge_raw": response.content or ""}
    except Exception as exc:
        logger.warning("llm_knowledge failed: %s", exc)
        return {"llm_knowledge_raw": ""}
