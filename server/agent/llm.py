"""LLM factory — OpenRouter-first with per-tier cost-optimized models.

Tiers (prices are $/M input / $/M output as of 2026-07):
- budget: cheap structured tasks — JSON decisions, outlines, supplementary
  prose. Default openai/gpt-5-nano ($0.05/$0.40).
- writer: long-form technical writing — merge, sections, patch fixes.
  Default google/gemini-2.5-flash ($0.30/$2.50), best quality-per-dollar.
- judge: LLM-as-judge critique. Default deepseek/deepseek-r1 ($0.70/$2.50) —
  reasoning model from a different family than the writer, which avoids
  self-preference bias when scoring.

Each tier carries an OpenRouter `models` fallback chain (tried in order on
rate-limit/downtime/moderation errors; billed for whichever actually served).
Per-tier overrides via OPENROUTER_MODEL_{BUDGET,WRITER,JUDGE} env vars.

When OPENROUTER_API_KEY is unset, falls back to direct Gemini via
GOOGLE_API_KEY (previous behaviour).
"""

import asyncio
import json
import logging
import re
from typing import Literal, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

from server.config import settings

logger = logging.getLogger(__name__)

Tier = Literal["budget", "writer", "judge"]

_DEFAULT_MODELS: dict[str, str] = {
    "budget": "openai/gpt-5-nano",
    "writer": "google/gemini-2.5-flash",
    "judge": "deepseek/deepseek-r1",
}

_FALLBACK_MODELS: dict[str, list[str]] = {
    "budget": ["google/gemini-2.5-flash-lite", "qwen/qwen3-30b-a3b"],
    "writer": ["openai/gpt-5-mini", "anthropic/claude-haiku-4.5"],
    "judge": ["openai/gpt-5-mini", "qwen/qwen3-30b-a3b"],
}

_GEMINI_DIRECT_MODEL = "gemini-2.5-flash"


def _tier_model(tier: Tier) -> str:
    override = {
        "budget": settings.OPENROUTER_MODEL_BUDGET,
        "writer": settings.OPENROUTER_MODEL_WRITER,
        "judge": settings.OPENROUTER_MODEL_JUDGE,
    }[tier]
    return override or _DEFAULT_MODELS[tier]


def get_llm(tier: Tier = "writer", temperature: float = 0.2) -> BaseChatModel:
    if settings.OPENROUTER_API_KEY:
        model = _tier_model(tier)
        fallbacks = [m for m in _FALLBACK_MODELS[tier] if m != model]
        return ChatOpenAI(
            model=model,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=temperature,
            default_headers={
                "HTTP-Referer": settings.CLIENT_URL,
                "X-Title": "gnostix-scribe",
            },
            extra_body={"models": fallbacks},
        )

    return ChatGoogleGenerativeAI(
        model=_GEMINI_DIRECT_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
    )


class LLMUnavailableError(RuntimeError):
    """All retries exhausted for a text LLM call."""


class LLMOutputError(RuntimeError):
    """The model kept returning output that failed schema validation."""


_CALL_TIMEOUT_S = 180.0
_RETRY_DELAYS_S = (1.0, 2.0, 4.0)


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for chunk in content:
            if isinstance(chunk, str):
                parts.append(chunk)
            elif isinstance(chunk, dict) and chunk.get("type") == "text":
                parts.append(chunk.get("text") or "")
        return "".join(parts)
    return str(content or "")


def _usage_of(response) -> dict:
    usage = getattr(response, "usage_metadata", None) or {}
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "calls": 1,
    }


def merge_usage(a: dict, b: dict) -> dict:
    """State reducer: sum per-node token usage dicts."""
    out = {k: dict(v) for k, v in (a or {}).items()}
    for node, usage in (b or {}).items():
        cur = out.setdefault(node, {})
        for key, val in usage.items():
            cur[key] = cur.get(key, 0) + val
    return out


def add_usage(a: dict, b: dict) -> dict:
    """Sum two flat usage dicts (input_tokens/output_tokens/calls)."""
    return {k: (a.get(k, 0) + b.get(k, 0)) for k in set(a) | set(b)}


async def invoke_text(
    tier: Tier, prompt: str, temperature: float = 0.2
) -> tuple[str, dict]:
    """Invoke with per-call timeout and exponential-backoff retries.

    Returns ``(text, usage)``. Raises LLMUnavailableError when every attempt
    fails — callers decide whether that is fatal for their node.
    """
    llm = get_llm(tier, temperature)
    last_exc: Exception | None = None
    for delay in (0.0, *_RETRY_DELAYS_S):
        if delay:
            await asyncio.sleep(delay)
        try:
            response = await asyncio.wait_for(
                llm.ainvoke(prompt), timeout=_CALL_TIMEOUT_S
            )
            return _content_to_text(response.content), _usage_of(response)
        except Exception as exc:
            last_exc = exc
            logger.warning("LLM call (tier=%s) failed: %s", tier, exc)
    raise LLMUnavailableError(f"tier '{tier}' unavailable after retries") from last_exc


_JSON_BLOB_RE = re.compile(r"\{.*\}|\[.*\]", re.DOTALL)

TModel = TypeVar("TModel", bound=BaseModel)


def _parse_model(text: str, schema: type[TModel]) -> TModel:
    match = _JSON_BLOB_RE.search(text or "")
    if not match:
        raise ValueError("no JSON object/array found in response")
    return schema.model_validate(json.loads(match.group(0)))


async def invoke_json(
    tier: Tier,
    prompt: str,
    schema: type[TModel],
    temperature: float = 0.1,
) -> tuple[TModel, dict]:
    """invoke_text + Pydantic validation, with one corrective re-ask.

    Raises LLMOutputError when the second attempt still fails validation;
    raises LLMUnavailableError when the underlying calls fail outright.
    """
    text, usage = await invoke_text(tier, prompt, temperature)
    try:
        return _parse_model(text, schema), usage
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        first_error = exc

    retry_prompt = (
        f"{prompt}\n\n"
        "============================================================\n"
        f"Your previous reply could not be parsed: {first_error}\n"
        f"Previous reply was:\n{text[:2000]}\n"
        "Reply again with ONLY the valid JSON — no commentary, no code fence."
    )
    text2, usage2 = await invoke_text(tier, retry_prompt, temperature)
    usage = add_usage(usage, usage2)
    try:
        return _parse_model(text2, schema), usage
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        raise LLMOutputError(f"schema validation failed twice: {exc}") from exc
