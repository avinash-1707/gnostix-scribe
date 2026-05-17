import asyncio
import logging

import trafilatura

from server.agent.state import AgentState

logger = logging.getLogger(__name__)


def _extract(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True,
        )
        return text or ""
    except Exception as exc:
        logger.warning("tpointtech_scraper extract failed for %s: %s", url, exc)
        return ""


async def tpointtech_scraper(state: AgentState) -> dict:
    url = state.get("tpointtech_url", "")
    if not url:
        return {"tpointtech_raw": ""}
    text = await asyncio.to_thread(_extract, url)
    return {"tpointtech_raw": text}
