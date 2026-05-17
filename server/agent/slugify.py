import re


_NON_ALNUM = re.compile(r"[^a-z0-9\s-]")
_WS_OR_DASH = re.compile(r"[\s_-]+")


def slugify(value: str) -> str:
    """Lowercase, strip non-alphanumerics, collapse whitespace/underscores into single hyphens."""
    value = value.strip().lower()
    value = _NON_ALNUM.sub("", value)
    value = _WS_OR_DASH.sub("-", value)
    return value.strip("-")
