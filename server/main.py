import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.auth.router import router as auth_router
from server.config import settings
from server.generation.janitor import sweep_loop, sweep_once
from server.generation.router import router as generation_router

logger = logging.getLogger(__name__)


def _checkpoint_conn_string() -> str:
    """DATABASE_URL is asyncpg-flavoured; psycopg wants plain postgresql://."""
    return settings.DATABASE_URL.replace("+asyncpg", "").replace(
        "ssl=require", "sslmode=require"
    )


def _enable_langsmith() -> None:
    """pydantic-settings reads server/.env without exporting it, but LangChain's
    tracer looks at os.environ — bridge the gap when a key is configured."""
    if not settings.LANGSMITH_API_KEY:
        return
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.LANGSMITH_PROJECT)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGSMITH_PROJECT)
    logger.info("LangSmith tracing enabled (project=%s)", settings.LANGSMITH_PROJECT)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _enable_langsmith()
    sweep_once()
    janitor_task = asyncio.create_task(sweep_loop(), name="output-janitor")

    saver_cm = None
    if settings.LANGGRAPH_CHECKPOINTS:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            from server.agent.graph import build_graph
            from server.generation.streaming import set_compiled_graph

            saver_cm = AsyncPostgresSaver.from_conn_string(_checkpoint_conn_string())
            saver = await saver_cm.__aenter__()
            await saver.setup()
            set_compiled_graph(build_graph(checkpointer=saver))
            logger.info("LangGraph Postgres checkpointing enabled")
        except Exception as exc:
            logger.warning(
                "LangGraph checkpointing unavailable, using in-memory graph: %s", exc
            )
            saver_cm = None

    try:
        yield
    finally:
        janitor_task.cancel()
        try:
            await janitor_task
        except asyncio.CancelledError:
            pass
        if saver_cm is not None:
            try:
                await saver_cm.__aexit__(None, None, None)
            except Exception as exc:
                logger.warning("checkpointer shutdown failed: %s", exc)


app = FastAPI(title="Gnostix Scribe API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CLIENT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(generation_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
