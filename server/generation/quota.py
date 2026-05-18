"""Per-user topic quota: count successful topics across history."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models import GenerationRecord


_SUCCESS_STATUSES = {"completed", "needs_review"}


async def count_successful_topics(session: AsyncSession, user_id: int) -> int:
    rows = await session.execute(
        select(GenerationRecord.mdx_outputs).where(
            GenerationRecord.user_id == user_id
        )
    )
    used = 0
    for (outputs,) in rows.all():
        for entry in outputs or []:
            if entry.get("status") in _SUCCESS_STATUSES:
                used += 1
    return used
