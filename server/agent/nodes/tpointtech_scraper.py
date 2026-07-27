import logging

from server.agent.scrape import scrape_source
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


async def tpointtech_scraper(state: AgentState) -> dict:
    topic = state.get("topic", "")
    fallback = state.get("tpointtech_url", "")
    if not topic and not fallback:
        return {"tpointtech_raw": "", "tpointtech_urls": []}
    text, used = await scrape_source("www.tpointtech.com", topic, fallback)
    return {"tpointtech_raw": text, "tpointtech_urls": used}
