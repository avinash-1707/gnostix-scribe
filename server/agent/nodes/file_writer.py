import logging
import re

from server.agent.slugify import slugify
from server.agent.state import AgentState
from server.config import settings

logger = logging.getLogger(__name__)


def _component_counts(mdx: str) -> dict[str, int]:
    return {
        "callout": len(re.findall(r"<Callout\b", mdx)),
        "figure": len(re.findall(r"<Figure\b", mdx)),
        "mermaid": len(re.findall(r"<Mermaid\b", mdx)),
        "embed": len(re.findall(r"<Embed\b", mdx)),
    }


async def file_writer(state: AgentState) -> dict:
    topic = state.get("topic", "untitled")
    topic_slug = state.get("topic_slug") or slugify(topic) or "untitled"
    mdx = state.get("mdx_draft", "")
    validation_ok = bool(state.get("validation_ok"))

    suffix = ".mdx" if validation_ok else "_NEEDS_REVIEW.mdx"
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = settings.OUTPUT_DIR / f"{topic_slug}{suffix}"
    path.write_text(mdx, encoding="utf-8")

    images = state.get("generated_images", [])
    no_code = re.sub(r"```.*?```", "", mdx, flags=re.DOTALL)
    word_count = len(re.findall(r"\b\w+\b", no_code))
    counts = _component_counts(mdx)
    logger.info(
        "file_writer: topic=%r path=%s words=%d images=%d figures=%d callouts=%d mermaid=%d embeds=%d needs_review=%s",
        topic, path, word_count, len(images),
        counts["figure"], counts["callout"], counts["mermaid"], counts["embed"],
        not validation_ok,
    )

    return {"output_path": str(path)}
