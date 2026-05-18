"""Sweep stale `output/content/*.mdx` files.

Files are normally deleted by `service.py` after a successful DB commit. Files
left behind by a final-commit failure or a crashed process are reaped here.
Default policy: anything older than 24h goes.
"""

import asyncio
import logging
import time

from server.config import settings

logger = logging.getLogger(__name__)


STALE_SECONDS = 24 * 60 * 60
SWEEP_INTERVAL_SECONDS = 60 * 60


def sweep_once() -> int:
    out_dir = settings.OUTPUT_DIR
    if not out_dir.exists():
        return 0
    now = time.time()
    deleted = 0
    for path in out_dir.glob("*.mdx"):
        try:
            age = now - path.stat().st_mtime
            if age >= STALE_SECONDS:
                path.unlink(missing_ok=True)
                deleted += 1
        except Exception as exc:
            logger.warning("janitor: failed to inspect %s: %s", path, exc)
    if deleted:
        logger.info("janitor: deleted %d stale .mdx file(s)", deleted)
    return deleted


async def sweep_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(sweep_once)
        except Exception as exc:
            logger.exception("janitor sweep failed: %s", exc)
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
