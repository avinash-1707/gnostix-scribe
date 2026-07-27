"""TTL disk cache for search resolutions and scraped pages.

Keeps the agent DB-free (architecture invariant): entries are JSON files under
``output/cache/<namespace>/<sha1>.json`` with mtime-based expiry. Only
non-empty values are cached so a throttled search can't poison a topic for a
full TTL. The janitor sweeps expired entries.
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path

from server.config import settings

logger = logging.getLogger(__name__)

CACHE_DIR: Path = settings.OUTPUT_DIR.parent / "cache"
TTL_S = 24 * 3600


def _path(namespace: str, key: str) -> Path:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / namespace / f"{digest}.json"


def _get_sync(namespace: str, key: str):
    path = _path(namespace, key)
    try:
        if time.time() - path.stat().st_mtime > TTL_S:
            return None
        return json.loads(path.read_text(encoding="utf-8"))["value"]
    except FileNotFoundError:
        return None
    except Exception as exc:
        logger.warning("cache read failed for %s: %s", path, exc)
        return None


def _put_sync(namespace: str, key: str, value) -> None:
    path = _path(namespace, key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"key": key, "value": value}), encoding="utf-8")
    except Exception as exc:
        logger.warning("cache write failed for %s: %s", path, exc)


async def cache_get(namespace: str, key: str):
    return await asyncio.to_thread(_get_sync, namespace, key)


async def cache_put(namespace: str, key: str, value) -> None:
    if not value:
        return
    await asyncio.to_thread(_put_sync, namespace, key, value)


def sweep_cache(ttl_s: int = TTL_S) -> int:
    """Delete expired cache entries. Returns count removed. Sync — call from
    the janitor's thread/loop."""
    removed = 0
    if not CACHE_DIR.exists():
        return 0
    cutoff = time.time() - ttl_s
    for path in CACHE_DIR.rglob("*.json"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            continue
    return removed
