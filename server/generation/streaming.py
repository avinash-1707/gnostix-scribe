"""Translate LangGraph node-level events into NodeEvent objects.

Listens to `compiled_graph.astream_events(version="v2")` and yields a
`(NodeEvent | None, final_state | None)` tuple per emission. The terminal yield
always has `NodeEvent=None` and carries the accumulated final state (or `None`
if the run did not reach `file_writer`).
"""

import logging
import time
from collections.abc import AsyncIterator

from server.agent.graph import compiled_graph
from server.agent.llm import merge_usage
from server.schemas import NodeEvent

logger = logging.getLogger(__name__)


NODE_NAMES = frozenset(
    {
        "topic_router",
        "gfg_scraper",
        "tpointtech_scraper",
        "llm_knowledge",
        "content_merger",
        "gap_filler",
        "outline_planner",
        "content_analyser",
        "image_generator",
        "mdx_generator",
        "mdx_validator",
        "mdx_fixer",
        "quality_judge",
        "file_writer",
    }
)


def _summarise(node: str, output: dict) -> str:
    if not isinstance(output, dict):
        return f"{node} done"
    if node == "topic_router":
        return f"resolved slug '{output.get('topic_slug', '')}'"
    if node == "gfg_scraper":
        return (
            f"GeeksForGeeks: {len(output.get('gfg_raw') or '')} chars "
            f"from {len(output.get('gfg_urls') or [])} page(s)"
        )
    if node == "tpointtech_scraper":
        return (
            f"TpointTech: {len(output.get('tpointtech_raw') or '')} chars "
            f"from {len(output.get('tpointtech_urls') or [])} page(s)"
        )
    if node == "llm_knowledge":
        return f"LLM knowledge: {len(output.get('llm_knowledge_raw') or '')} chars"
    if node == "content_merger":
        return (
            f"merged {len(output.get('merged_content') or '')} chars "
            f"(coverage_ok={output.get('coverage_ok')})"
        )
    if node == "gap_filler":
        return f"gap-fill content: {len(output.get('gap_content') or '')} chars"
    if node == "outline_planner":
        n = len((output.get("outline") or {}).get("sections") or [])
        return f"planned {n} sections"
    if node == "content_analyser":
        n = len(output.get("image_requests") or [])
        return f"needs_images={output.get('needs_images')} ({n} requests)"
    if node == "image_generator":
        return f"generated {len(output.get('generated_images') or [])} image(s)"
    if node == "mdx_generator":
        return (
            f"draft {len(output.get('mdx_draft') or '')} chars "
            f"(attempt {output.get('generation_attempts')})"
        )
    if node == "mdx_validator":
        errs = output.get("validation_errors") or []
        return "validation OK" if output.get("validation_ok") else f"failed ({len(errs)} issues)"
    if node == "mdx_fixer":
        return (
            f"patched draft to {len(output.get('mdx_draft') or '')} chars "
            f"(attempt {output.get('generation_attempts')})"
        )
    if node == "quality_judge":
        overall = output.get("judge_overall")
        notes = output.get("revision_notes") or []
        if not output.get("judge_scores"):
            return "judge unavailable — passed through"
        verdict = f"needs revision ({len(notes)} notes)" if notes else "approved"
        return f"score {overall}/10 — {verdict}"
    if node == "file_writer":
        return f"wrote {output.get('output_path', '')}"
    return f"{node} done"


async def stream_topic(
    topic: str,
) -> AsyncIterator[tuple[NodeEvent | None, dict | None]]:
    start = time.perf_counter()
    node_starts: dict[str, float] = {}
    collected: dict = {}

    try:
        async for ev in compiled_graph.astream_events({"topic": topic}, version="v2"):
            kind = ev.get("event", "")
            name = ev.get("name", "")
            if name not in NODE_NAMES:
                continue

            if kind == "on_chain_start":
                node_starts[name] = time.perf_counter()
                yield (
                    NodeEvent(
                        node=name,
                        status="running",
                        message=f"{name} started",
                        elapsed_ms=int((time.perf_counter() - start) * 1000),
                        topic=topic,
                    ),
                    None,
                )

            elif kind == "on_chain_end":
                output = ev.get("data", {}).get("output") or {}
                if isinstance(output, dict):
                    # Reducer-backed keys accumulate; plain keys overwrite.
                    for key, value in output.items():
                        if key == "token_usage":
                            collected["token_usage"] = merge_usage(
                                collected.get("token_usage", {}), value
                            )
                        elif key == "warnings":
                            collected.setdefault("warnings", []).extend(value)
                        else:
                            collected[key] = value
                node_elapsed = int(
                    (time.perf_counter() - node_starts.get(name, start)) * 1000
                )
                yield (
                    NodeEvent(
                        node=name,
                        status="done",
                        message=_summarise(name, output if isinstance(output, dict) else {}),
                        elapsed_ms=node_elapsed,
                        topic=topic,
                    ),
                    None,
                )

            elif kind == "on_chain_error":
                err = ev.get("data", {}).get("error", "unknown")
                yield (
                    NodeEvent(
                        node=name,
                        status="error",
                        message=str(err),
                        elapsed_ms=int((time.perf_counter() - start) * 1000),
                        topic=topic,
                    ),
                    None,
                )
    except Exception as exc:
        logger.exception("stream_topic crashed for %r", topic)
        yield (
            NodeEvent(
                node="ERROR",
                status="error",
                message=str(exc),
                elapsed_ms=int((time.perf_counter() - start) * 1000),
                topic=topic,
            ),
            None,
        )
        yield None, None
        return

    final_state = collected if collected.get("output_path") else None
    yield None, final_state
