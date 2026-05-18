"""Database lifecycle for generation_records + commit-then-delete file flow.

`commit_topic_output_then_delete` is the canonical retry buffer step from the
architecture spec: the on-disk MDX is only removed after a successful DB commit.
On commit failure the file is retained and the next attempt re-reads from disk
without re-running the agent.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from server.models import GenerationRecord

logger = logging.getLogger(__name__)


_COMMIT_RETRIES = 3
_COMMIT_BACKOFF_BASE = 0.5


async def create_record(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: int,
    topics: list[str],
) -> int:
    async with session_factory() as session:
        rec = GenerationRecord(
            user_id=user_id,
            topics=topics,
            mdx_outputs=[],
            overall_status="running",
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return rec.id


async def _patch_record(
    session_factory: async_sessionmaker[AsyncSession],
    record_id: int,
    *,
    mdx_outputs: list[dict] | None = None,
    overall_status: str | None = None,
    mark_completed: bool = False,
) -> None:
    async with session_factory() as session:
        rec = await session.get(GenerationRecord, record_id)
        if rec is None:
            logger.warning("generation_record %s vanished before update", record_id)
            return
        if mdx_outputs is not None:
            rec.mdx_outputs = mdx_outputs
        if overall_status is not None:
            rec.overall_status = overall_status
        if mark_completed:
            rec.completed_at = datetime.now(timezone.utc)
        await session.commit()


async def commit_topic_output_then_delete(
    session_factory: async_sessionmaker[AsyncSession],
    record_id: int,
    mdx_outputs: list[dict],
    output_path: str,
) -> bool:
    delay = _COMMIT_BACKOFF_BASE
    last_exc: Exception | None = None
    committed = False
    for attempt in range(1, _COMMIT_RETRIES + 1):
        try:
            await _patch_record(session_factory, record_id, mdx_outputs=mdx_outputs)
            committed = True
            break
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "commit_topic_output attempt %d/%d failed: %s",
                attempt, _COMMIT_RETRIES, exc,
            )
            if attempt < _COMMIT_RETRIES:
                await asyncio.sleep(delay)
                delay *= 2

    if not committed:
        logger.error(
            "commit_topic_output FINAL failure; file retained at %s: %s",
            output_path, last_exc,
        )
        return False

    if output_path:
        try:
            await asyncio.to_thread(Path(output_path).unlink, True)
        except Exception as exc:
            logger.warning("post-commit delete failed for %s: %s", output_path, exc)
    return True


async def finalize_record(
    session_factory: async_sessionmaker[AsyncSession],
    record_id: int,
    overall_status: str,
) -> None:
    await _patch_record(
        session_factory,
        record_id,
        overall_status=overall_status,
        mark_completed=True,
    )
