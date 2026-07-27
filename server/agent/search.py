"""Search-based URL resolution for scraper targets.

Slug-guessed URLs (``geeksforgeeks.org/<slug>/``) rarely match real article
slugs, so scrapers first resolve URLs via DuckDuckGo's HTML endpoint with a
``site:`` query. DDG throttles bursts with an HTTP 202 challenge page, so all
queries are serialised through a global lock with minimum spacing, and 202s
are retried with backoff. On total failure the caller falls back to the slug
guess, and the gap_filler/llm_knowledge nodes compensate for thin scrapes.
"""

import asyncio
import logging
import re
import time
from urllib.parse import quote_plus, unquote, urlparse

import httpx

logger = logging.getLogger(__name__)

_DDG_URL = "https://html.duckduckgo.com/html/?q={query}"
_UDDG_RE = re.compile(r"uddg=([^&\"'<>]+)")
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
    )
}
_TIMEOUT = httpx.Timeout(10.0)

_MIN_SPACING_S = 3.0
_RETRY_DELAYS_S = (3.0, 6.0)

_lock = asyncio.Lock()
_last_call = 0.0


async def _fetch_spaced(url: str) -> tuple[int, str]:
    """GET with a global minimum spacing between DDG requests."""
    global _last_call
    async with _lock:
        wait = _MIN_SPACING_S - (time.monotonic() - _last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True
            ) as client:
                resp = await client.get(url)
                return resp.status_code, resp.text
        finally:
            _last_call = time.monotonic()


def _filter_urls(candidates: list[str], site: str, limit: int) -> list[str]:
    bare = site.removeprefix("www.")
    urls: list[str] = []
    for url in candidates:
        host = urlparse(url).netloc.removeprefix("www.")
        if host != bare:
            continue
        if url not in urls:
            urls.append(url)
        if len(urls) >= limit:
            break
    return urls


async def resolve_urls(site: str, topic: str, limit: int = 2) -> list[str]:
    """Return up to ``limit`` article URLs on ``site`` for ``topic``.

    ``site`` is a bare domain like ``www.geeksforgeeks.org``. Returns an empty
    list on total failure — the caller decides the fallback.
    """
    query = quote_plus(f"site:{site} {topic}")
    url = _DDG_URL.format(query=query)

    for attempt, delay in enumerate((0.0, *_RETRY_DELAYS_S)):
        if delay:
            await asyncio.sleep(delay)
        try:
            status, html = await _fetch_spaced(url)
        except Exception as exc:
            logger.warning("resolve_urls(%s, %r) fetch failed: %s", site, topic, exc)
            return []
        if status == 200:
            candidates = [unquote(m.group(1)) for m in _UDDG_RE.finditer(html)]
            return _filter_urls(candidates, site, limit)
        logger.info(
            "resolve_urls(%s): ddg throttled (%d), attempt %d/3",
            site, status, attempt + 1,
        )

    logger.warning("resolve_urls(%s, %r): ddg throttled on all attempts", site, topic)
    return []
