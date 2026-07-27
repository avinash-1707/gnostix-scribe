import logging
import re

import frontmatter

from server.agent.state import AgentState

logger = logging.getLogger(__name__)


VALID_CALLOUT_TYPES = {"tip", "note", "info", "warn", "danger"}
RAW_HTML_TAGS = {"html", "body", "head", "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6"}

_FENCE_RE = re.compile(r"(?m)^([ \t]*)```([A-Za-z0-9_+\-]*)\s*$")
_HEADING_RE = re.compile(r"(?m)^#{1,6} .+")
_INTRO_RE = re.compile(r"(?m)^#\s+Introduction\b")
_SUMMARY_RE = re.compile(r"(?m)^##\s+(Summary|Conclusion)\b")
_SECTION_RE = re.compile(r"(?m)^##\s+.+")
_CALLOUT_RE = re.compile(r"<Callout\b([^>]*)>", re.IGNORECASE)
_FIGURE_RE = re.compile(r"<Figure\b([^>]*)/?>", re.IGNORECASE)
_MERMAID_RE = re.compile(r"<Mermaid\b([^>]*)/?>", re.IGNORECASE)
_VIDEO_RE = re.compile(r"<Video\b[^>]*>", re.IGNORECASE)
_TYPE_ATTR_RE = re.compile(r"type\s*=\s*[\"']([^\"']+)[\"']")
_ALT_ATTR_RE = re.compile(r"alt\s*=\s*[\"']([^\"']*)[\"']")
_SRC_ATTR_RE = re.compile(r"src\s*=\s*[\"']([^\"']+)[\"']")
_RAW_HTML_RE = re.compile(r"<(/?)(\w+)\b")


def _word_count_excluding_code(text: str) -> int:
    no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return len(re.findall(r"\b\w+\b", no_code))


def _check_frontmatter(mdx: str) -> tuple[dict, str, list[str]]:
    errors: list[str] = []
    if not mdx.strip().startswith("---"):
        errors.append("Frontmatter block missing (--- ... ---)")
        return {}, mdx, errors
    try:
        post = frontmatter.loads(mdx)
    except Exception as exc:
        errors.append(f"Frontmatter parse error: {exc}")
        return {}, mdx, errors

    meta = dict(post.metadata)
    if not str(meta.get("title", "")).strip():
        errors.append("frontmatter.title missing or empty")
    if not str(meta.get("description", "")).strip():
        errors.append("frontmatter.description missing or empty")
    tags = meta.get("tags")
    if not isinstance(tags, list) or not tags:
        errors.append("frontmatter.tags missing or not a non-empty list")
    return meta, post.content, errors


def _check_structure(body: str) -> list[str]:
    errors: list[str] = []
    if not _SECTION_RE.search(body):
        errors.append("Document contains no ## section heading")
    if not _INTRO_RE.search(body):
        errors.append("Missing '# Introduction' heading")
    if not _SUMMARY_RE.search(body):
        errors.append("Missing '## Summary' (or '## Conclusion') heading")
    return errors


def _check_code_fences(body: str) -> list[str]:
    errors: list[str] = []
    fences = list(_FENCE_RE.finditer(body))
    if len(fences) % 2 != 0:
        errors.append("Unclosed fenced code block detected")
    for idx in range(0, len(fences) - 1, 2):
        opening = fences[idx]
        lang = opening.group(2).strip()
        if not lang:
            line_no = body[: opening.start()].count("\n") + 1
            errors.append(f"Code block at line {line_no} has no language tag")
    return errors


def _check_callouts(body: str) -> list[str]:
    errors: list[str] = []
    for m in _CALLOUT_RE.finditer(body):
        attrs = m.group(1)
        tm = _TYPE_ATTR_RE.search(attrs)
        if not tm:
            errors.append("<Callout> missing type attribute")
            continue
        if tm.group(1).lower() not in VALID_CALLOUT_TYPES:
            errors.append(f"<Callout> has invalid type='{tm.group(1)}'")
    return errors


def _check_figures(body: str, image_srcs: set[str]) -> list[str]:
    errors: list[str] = []
    for m in _FIGURE_RE.finditer(body):
        attrs = m.group(1)
        alt_m = _ALT_ATTR_RE.search(attrs)
        if not alt_m or not alt_m.group(1).strip():
            errors.append("<Figure> missing non-empty alt attribute")
        src_m = _SRC_ATTR_RE.search(attrs)
        if not src_m:
            errors.append("<Figure> missing src attribute")
            continue
        src = src_m.group(1).strip()
        if image_srcs and src not in image_srcs:
            errors.append(f"<Figure src='{src}'> not in generated_images list")
    return errors


def _check_mermaid(body: str) -> list[str]:
    errors: list[str] = []
    for m in _MERMAID_RE.finditer(body):
        attrs = m.group(1)
        if "chart" not in attrs:
            errors.append("<Mermaid> missing chart attribute")
    return errors


def _check_video(body: str) -> list[str]:
    if _VIDEO_RE.search(body):
        return ["<Video> component used but no video assets are provided"]
    return []


def _strip_jsx_and_code(body: str) -> str:
    no_code = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    no_jsx = re.sub(r"<(Callout|Figure|Mermaid|Embed|Video)\b[^>]*>.*?(?:</\1>|/>)", "", no_code, flags=re.DOTALL)
    no_jsx = re.sub(r"<(Callout|Figure|Mermaid|Embed|Video)\b[^>]*/?>", "", no_jsx)
    return no_jsx


def _check_raw_html(body: str) -> list[str]:
    errors: list[str] = []
    scan = _strip_jsx_and_code(body)
    seen: set[str] = set()
    for m in _RAW_HTML_RE.finditer(scan):
        tag = m.group(2).lower()
        if tag in RAW_HTML_TAGS and tag not in seen:
            errors.append(f"Raw HTML tag <{tag}> not allowed outside JSX components")
            seen.add(tag)
    return errors


_FENCE_LINE_RE = re.compile(r"^([ \t]*)```([A-Za-z0-9_+\-]*)\s*$")


def _auto_fix(mdx: str) -> str:
    """Deterministically repair mechanical issues before burning an LLM retry:
    opening fences without a language tag get ``text``; an unclosed final fence
    gets closed."""
    lines = mdx.split("\n")
    in_fence = False
    for i, line in enumerate(lines):
        m = _FENCE_LINE_RE.match(line)
        if not m:
            continue
        if not in_fence and not m.group(2).strip():
            lines[i] = f"{m.group(1)}```text"
        in_fence = not in_fence
    if in_fence:
        lines.append("```")
    return "\n".join(lines)


def _validate(mdx: str, image_srcs: set[str]) -> list[str]:
    if not mdx or not mdx.strip():
        return ["MDX draft is empty"]
    meta, body, errors = _check_frontmatter(mdx)
    errors += _check_structure(body)
    errors += _check_code_fences(body)
    errors += _check_callouts(body)
    errors += _check_figures(body, image_srcs)
    errors += _check_mermaid(body)
    errors += _check_video(body)
    errors += _check_raw_html(body)
    if _word_count_excluding_code(body) < 500:
        errors.append("Document is under 500 words (excluding code blocks)")
    return errors


async def mdx_validator(state: AgentState) -> dict:
    mdx = state.get("mdx_draft", "")
    images = state.get("generated_images", [])
    image_srcs = {img["src"] for img in images if img.get("src")}

    fixed = _auto_fix(mdx) if mdx.strip() else mdx
    if fixed != mdx:
        logger.info("mdx_validator auto-fixed mechanical issues")

    errors = _validate(fixed, image_srcs)
    result = {
        "validation_ok": len(errors) == 0,
        "validation_errors": errors,
    }
    if fixed != mdx:
        result["mdx_draft"] = fixed
    return result
