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


async def run_generation(user_id: int, topics_raw: str) -> AsyncIterator[str]:
    """Async generator of SSE-formatted chunks for the given user + topics."""
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

    for topic in topics:
        final_state: dict | None = None

        async for event, state in stream_topic(topic):
            if event is not None:
                yield format_event(event)
                if event.status == "error":
                    saw_failure = True
            if state is not None:
                final_state = state

        if not final_state or not final_state.get("output_path"):
            saw_failure = True
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
            yield format_event(
                NodeEvent(node="ERROR", status="error",
                          message="agent did not produce output",
                          elapsed_ms=0, topic=topic)
            )
            continue

        output_path = final_state["output_path"]
        try:
            mdx_text = await _read_mdx(output_path)
        except Exception as exc:
            logger.error("read mdx failed for %s: %s", output_path, exc)
            mdx_text = ""

        entry = _build_output_entry(topic, mdx_text, final_state)
        collected_outputs.append(entry)

        ok = await commit_topic_output_then_delete(
            AsyncSessionLocal, record_id, collected_outputs, output_path,
        )
        if not ok:
            saw_failure = True
            yield format_event(
                NodeEvent(node="ERROR", status="error",
                          message="DB commit failed; file retained for retry",
                          elapsed_ms=0, topic=topic)
            )
            continue

        if entry["status"] != "completed":
            saw_failure = True
        yield format_event(
            NodeEvent(node="DONE", status="done",
                      message=mdx_text, elapsed_ms=0, topic=topic)
        )

    final_status = "partial" if saw_failure else "completed"
    try:
        await finalize_record(AsyncSessionLocal, record_id, final_status)
    except Exception as exc:
        logger.error("finalize_record failed for %s: %s", record_id, exc)
