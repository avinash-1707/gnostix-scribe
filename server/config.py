from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CLOUDINARY_URL: str = ""

    # OpenRouter — when set, all text LLM calls route through it with per-tier
    # models; when empty, falls back to direct Gemini via GOOGLE_API_KEY.
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL_BUDGET: str = ""  # defaults set in agent/llm.py
    OPENROUTER_MODEL_WRITER: str = ""
    OPENROUTER_MODEL_JUDGE: str = ""
    OPENROUTER_MODEL_IMAGE: str = ""  # default set in agent/nodes/image_generator.py

    CLIENT_URL: str = "http://localhost:3001"

    OUTPUT_DIR: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "output" / "content"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
