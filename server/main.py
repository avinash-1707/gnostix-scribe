import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.auth.router import router as auth_router
from server.config import settings
from server.generation.janitor import sweep_loop, sweep_once
from server.generation.router import router as generation_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sweep_once()
    janitor_task = asyncio.create_task(sweep_loop(), name="output-janitor")
    try:
        yield
    finally:
        janitor_task.cancel()
        try:
            await janitor_task
        except asyncio.CancelledError:
            pass


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
