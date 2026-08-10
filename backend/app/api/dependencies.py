import re
from typing import Annotated, AsyncGenerator

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal

WORKSPACE_HEADER = "X-Workspace-Id"
WORKSPACE_RE = re.compile(r"^[a-zA-Z0-9_-]{8,120}$")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_workspace_id(
    workspace_id: Annotated[str | None, Header(alias=WORKSPACE_HEADER)] = None,
) -> str:
    if not workspace_id or not WORKSPACE_RE.fullmatch(workspace_id):
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid {WORKSPACE_HEADER} header",
        )
    return workspace_id