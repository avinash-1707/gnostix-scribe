import operator
from typing import Annotated, TypedDict

from server.agent.llm import merge_usage


class AgentState(TypedDict, total=False):
    topic: str
    topic_slug: str

    gfg_url: str
    tpointtech_url: str
    gfg_urls: list[str]
    tpointtech_urls: list[str]

    gfg_raw: str
    tpointtech_raw: str
    llm_knowledge_raw: str

    merged_content: str
    coverage_ok: bool
    gap_content: str

    outline: dict

    needs_images: bool
    image_requests: list[dict]
    generated_images: list[dict]

    mdx_draft: str
    validation_errors: list[str]
    validation_ok: bool

    judge_scores: dict
    judge_overall: float
    judge_attempts: int
    revision_notes: list[str]

    scrape_attempts: int
    generation_attempts: int

    # Reducer-backed accumulators: parallel nodes may write these concurrently.
    warnings: Annotated[list[str], operator.add]
    token_usage: Annotated[dict, merge_usage]

    output_path: str
