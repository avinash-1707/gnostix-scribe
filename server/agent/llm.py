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

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from server.config import settings

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
