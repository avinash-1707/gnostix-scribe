"""Shared scraping helpers used by the gfg/tpointtech scraper nodes."""

import asyncio
import logging

import trafilatura

from server.agent.search import resolve_urls

logger = logging.getLogger(__name__)

MAX_CHARS_PER_PAGE = 20_000
PAGES_PER_SOURCE = 2


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
        logger.warning("extract failed for %s: %s", url, exc)
        return ""


async def scrape_source(site: str, topic: str, fallback_url: str) -> tuple[str, list[str]]:
    """Resolve real article URLs via search, scrape them, concatenate.

    Falls back to the slug-guessed ``fallback_url`` when search yields nothing.
    Returns ``(combined_text, urls_used)``.
    """
    urls = await resolve_urls(site, topic, limit=PAGES_PER_SOURCE)
    if not urls and fallback_url:
        urls = [fallback_url]

    texts = await asyncio.gather(*(asyncio.to_thread(_extract, u) for u in urls))
    parts = []
    used: list[str] = []
    for url, text in zip(urls, texts):
        if text:
            parts.append(text[:MAX_CHARS_PER_PAGE])
            used.append(url)
    return "\n\n---\n\n".join(parts), used
