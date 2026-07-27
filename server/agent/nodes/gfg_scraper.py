import logging

from server.agent.scrape import scrape_source
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


async def gfg_scraper(state: AgentState) -> dict:
    topic = state.get("topic", "")
    fallback = state.get("gfg_url", "")
    if not topic and not fallback:
        return {"gfg_raw": "", "gfg_urls": []}
    text, used = await scrape_source("www.geeksforgeeks.org", topic, fallback)
    return {"gfg_raw": text, "gfg_urls": used}
