from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from app.db import StatusTask, Task
from core.schemas.task import TaskCreate, TaskRead, TaskUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logging import logger


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_by_id(self, key: int) -> Task:
        task = await self.session.get(Task, key)
        if not task:
            logger.warning(f"Task with id {key} not found")
            raise HTTPException(status_code=404, detail=f"Task with id {key} not found")
        return task

    async def create_task(self, task: TaskCreate) -> TaskRead:
        task = Task(
            title=task.title,
            description=task.description,
            status=StatusTask.NEW_TASK
        )
        await self.session.add(task)
        await self.session.commit()
        return TaskRead.model_validate(task, from_attributes=True)

    async def get_task(self, task_id: int) -> TaskRead:
        result = await self._get_by_id(task_id)
        return TaskRead.model_validate(result, from_attributes=True)
        
    async def get_tasks(self, status: Optional[StatusTask] = None) -> List[TaskRead]:
        query = select(Task)
        if status:
            query = query.filter(Task.status == status)
        results = (await self.session.execute(query)).all()
        return [TaskRead.model_validate(result, from_attributes=True) for result in results]

    async def update_task(self, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        task = await self._get_by_id(task_id)
        update_data = task_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        
        await self.session.commit()
        await self.session.refresh(task)
        return TaskRead.model_validate(task, from_attributes=True)
