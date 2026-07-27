"""Top-level generation orchestrator: parse topics, run agent per topic,
emit SSE chunks, persist record incrementally, manage concurrency slot.
"""

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from pathlib import Path

from server.database import AsyncSessionLocal
from server.generation.persistence import (
    commit_topic_output_then_delete,
    create_record,
    finalize_record,
)
from server.generation.sse import format_event
from server.generation.streaming import stream_topic
from server.schemas import NodeEvent

logger = logging.getLogger(__name__)


class ConcurrentGenerationError(Exception):
    pass


_active_users: set[int] = set()
_active_lock = asyncio.Lock()


async def acquire_slot(user_id: int) -> None:
    async with _active_lock:
        if user_id in _active_users:
            raise ConcurrentGenerationError()
        _active_users.add(user_id)


async def release_slot(user_id: int) -> None:
    async with _active_lock:
        _active_users.discard(user_id)


_TOPIC_SPLIT_RE = re.compile(r"[\n,]")


def parse_topics(raw: str) -> list[str]:
    parts = _TOPIC_SPLIT_RE.split(raw or "")
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        topic = part.strip()
        if topic and topic not in seen:
            seen.add(topic)
            out.append(topic)
    return out


async def _read_mdx(path: str) -> str:
    return await asyncio.to_thread(Path(path).read_text, encoding="utf-8")


def _build_output_entry(
    topic: str, mdx_text: str, final_state: dict
) -> dict:
    images = final_state.get("generated_images") or []
    status = "completed" if final_state.get("validation_ok") else "needs_review"
    return {
        "topic": topic,
        "mdx": mdx_text,
        "status": status,
        "cloudinary_image_urls": [img["src"] for img in images if img.get("src")],
        "token_usage": final_state.get("token_usage") or {},
        "judge_scores": final_state.get("judge_scores") or {},
        "warnings": final_state.get("warnings") or [],
    }


MAX_PARALLEL_TOPICS = 2


async def run_generation(user_id: int, topics_raw: str) -> AsyncIterator[str]:
    """Async generator of SSE-formatted chunks for the given user + topics.

    Topics run concurrently (bounded by MAX_PARALLEL_TOPICS); their events are
    merged into one stream via a queue. The client demultiplexes by the
    ``topic`` field. DB commits are serialised — collected_outputs is reassigned
    wholesale on each commit, so concurrent commits would lose updates.
    """
    topics = parse_topics(topics_raw)
    if not topics:
        yield format_event(
            NodeEvent(node="ERROR", status="error",
                      message="no topics provided", elapsed_ms=0, topic="")
        )
        return

    record_id = await create_record(AsyncSessionLocal, user_id, topics)
    collected_outputs: list[dict] = []
    saw_failure = False
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    commit_lock = asyncio.Lock()
    sem = asyncio.Semaphore(MAX_PARALLEL_TOPICS)

    async def run_topic(topic: str) -> None:
        nonlocal saw_failure
        async with sem:
            final_state: dict | None = None
            try:
                async for event, state in stream_topic(topic):
                    if event is not None:
                        await queue.put(format_event(event))
                        if event.status == "error":
                            saw_failure = True
                    if state is not None:
                        final_state = state
            except Exception as exc:
                logger.exception("stream_topic crashed for %r", topic)
                saw_failure = True
                final_state = None

            if not final_state or not final_state.get("output_path"):
                saw_failure = True
                async with commit_lock:
                    collected_outputs.append(
                        {"topic": topic, "mdx": "", "status": "failed",
                         "cloudinary_image_urls": []}
                    )
                    try:
                        await commit_topic_output_then_delete(
                            AsyncSessionLocal, record_id, collected_outputs, "",
                        )
                    except Exception as exc:
                        logger.error("commit failed topic record after agent failure: %s", exc)
                await queue.put(format_event(
                    NodeEvent(node="ERROR", status="error",
                              message="agent did not produce output",
                              elapsed_ms=0, topic=topic)
                ))
                return

            output_path = final_state["output_path"]
            try:
                mdx_text = await _read_mdx(output_path)
            except Exception as exc:
                logger.error("read mdx failed for %s: %s", output_path, exc)
                mdx_text = ""

            entry = _build_output_entry(topic, mdx_text, final_state)
            async with commit_lock:
                collected_outputs.append(entry)
                ok = await commit_topic_output_then_delete(
                    AsyncSessionLocal, record_id, collected_outputs, output_path,
                )
            if not ok:
                saw_failure = True
                await queue.put(format_event(
                    NodeEvent(node="ERROR", status="error",
                              message="DB commit failed; file retained for retry",
                              elapsed_ms=0, topic=topic)
                ))
                return

            if entry["status"] != "completed":
                saw_failure = True
            await queue.put(format_event(
                NodeEvent(node="DONE", status="done",
                          message=mdx_text, elapsed_ms=0, topic=topic)
            ))

    async def drive() -> None:
        try:
            await asyncio.gather(*(run_topic(t) for t in topics))
        finally:
            await queue.put(None)

    driver = asyncio.create_task(drive())
    try:
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
        await driver
    finally:
        driver.cancel()

    final_status = "partial" if saw_failure else "completed"
    try:
        await finalize_record(AsyncSessionLocal, record_id, final_status)
    except Exception as exc:
        logger.error("finalize_record failed for %s: %s", record_id, exc)
