from typing import TypedDict


class AgentState(TypedDict, total=False):
    topic: str
    topic_slug: str

    gfg_url: str
    tpointtech_url: str

    gfg_raw: str
    tpointtech_raw: str
    llm_knowledge_raw: str

    merged_content: str
    coverage_ok: bool

    needs_images: bool
    image_requests: list[dict]
    generated_images: list[dict]

    mdx_draft: str
    validation_errors: list[str]
    validation_ok: bool

    scrape_attempts: int
    generation_attempts: int

    output_path: str
