from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.auth.router import router as auth_router
from server.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Gnostix Scribe API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CLIENT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
