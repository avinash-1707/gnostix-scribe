"""Standalone test driver for the LangGraph MDX agent.

Run from repo root:
    server/.venv/bin/python scripts/run_agent.py "Binary Search"
"""

import asyncio
import logging
import sys

from server.agent.graph import compiled_graph


async def run(topic: str) -> None:
    state = await compiled_graph.ainvoke({"topic": topic})
    print("=" * 60)
    print(f"topic:           {state.get('topic')!r}")
    print(f"topic_slug:      {state.get('topic_slug')!r}")
    print(f"scrape_attempts: {state.get('scrape_attempts')}")
    print(f"coverage_ok:     {state.get('coverage_ok')}")
    print(f"needs_images:    {state.get('needs_images')}")
    print(f"images:          {len(state.get('generated_images') or [])}")
    print(f"gen_attempts:    {state.get('generation_attempts')}")
    print(f"validation_ok:   {state.get('validation_ok')}")
    if state.get("validation_errors"):
        print("validation_errors:")
        for err in state["validation_errors"]:
            print(f"  - {err}")
    print(f"output_path:     {state.get('output_path')}")
    print("=" * 60)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    )
    topic = sys.argv[1] if len(sys.argv) > 1 else "Binary Search"
    asyncio.run(run(topic))


if __name__ == "__main__":
    main()
