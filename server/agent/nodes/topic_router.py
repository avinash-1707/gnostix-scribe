from server.agent.slugify import slugify
from server.agent.state import AgentState


def topic_router(state: AgentState) -> dict:
    """Validate the topic, build scraper URLs, initialise state fields."""
    topic = (state.get("topic") or "").strip()
    if not topic:
        raise ValueError("topic_router: topic must be a non-empty string")

    slug = slugify(topic)
    return {
        "topic": topic,
        "topic_slug": slug,
        "gfg_url": f"https://www.geeksforgeeks.org/{slug}/",
        "tpointtech_url": f"https://www.tpointtech.com/{slug}/",
        "gfg_urls": [],
        "tpointtech_urls": [],
        "gfg_raw": "",
        "tpointtech_raw": "",
        "llm_knowledge_raw": "",
        "merged_content": "",
        "coverage_ok": False,
        "gap_content": "",
        "outline": {},
        "needs_images": False,
        "image_requests": [],
        "generated_images": [],
        "mdx_draft": "",
        "validation_errors": [],
        "validation_ok": False,
        "judge_scores": {},
        "judge_overall": 0.0,
        "judge_attempts": 0,
        "revision_notes": [],
        "scrape_attempts": 0,
        "generation_attempts": 0,
        "output_path": "",
    }
