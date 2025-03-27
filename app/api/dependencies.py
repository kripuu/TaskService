from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.core.service.task import TaskService

async def task_service(
    session: AsyncSession = Depends(get_session)
) -> TaskService:
    return TaskService(session) 