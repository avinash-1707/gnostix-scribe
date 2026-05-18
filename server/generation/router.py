from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.dependencies import CurrentUser
from server.auth.service import decode_token
from server.database import get_async_session
from server.generation.service import (
    ConcurrentGenerationError,
    acquire_slot,
    release_slot,
    run_generation,
)
from server.models import GenerationRecord, User
from server.schemas import GenerationRecordOut

router = APIRouter(tags=["generation"])


async def _resolve_user_from_query_token(token: str, session: AsyncSession) -> User:
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc),
        ) from exc
    user = await session.scalar(select(User).where(User.id == int(payload["sub"])))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found",
        )
    return user


@router.get("/generate")
async def generate(
    topics: Annotated[str, Query(min_length=1, description="raw textarea string; split on newlines and commas")],
    token: Annotated[str, Query(min_length=1, description="access token (EventSource cannot send custom headers)")],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> StreamingResponse:
    user = await _resolve_user_from_query_token(token, session)

    try:
        await acquire_slot(user.id)
    except ConcurrentGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="a generation is already running for this user",
        ) from exc

    async def event_stream():
        try:
            async for chunk in run_generation(user.id, topics):
                yield chunk
        finally:
            await release_slot(user.id)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history", response_model=list[GenerationRecordOut])
async def list_history(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[GenerationRecord]:
    result = await session.execute(
        select(GenerationRecord)
        .where(GenerationRecord.user_id == current_user.id)
        .order_by(GenerationRecord.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/history/{record_id}", response_model=GenerationRecordOut)
async def get_record(
    record_id: int,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> GenerationRecord:
    rec = await session.get(GenerationRecord, record_id)
    if rec is None or rec.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="record not found",
        )
    return rec
