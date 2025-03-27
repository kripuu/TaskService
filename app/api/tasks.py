from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.dependencies import task_service
from app.core.schemas.task import TaskCreate, TaskRead
from app.core.service.task import TaskService
from app.db import StatusTask
from app.message.producer import publish_task
from app.utils.logging import logger


task_router = APIRouter()

@task_router.post("/", response_model=TaskRead, tags=["Tasks"], description="Публикация задачи")
async def create_task(task: TaskCreate, service: Annotated[TaskService, Depends(task_service)]):
    logger.info(f"Creating new task: {task.title}")
    db_task = service.create_task(task)

    # Отправляем задачу в очередь для обработки
    await publish_task(db_task.id)
    
    return db_task

@task_router.get("/{task_id}", response_model=TaskRead, tags=["Tasks"], description="Получение информации о задаче")
def get_task(task_id: int, service: Annotated[TaskService, Depends(task_service)]):
    return service.get_task(task_id)

@task_router.get("/", response_model=list[TaskRead], tags=["Tasks"], description="Получение списка задач")
def get_tasks(
    service: Annotated[TaskService, Depends(task_service)],
    status: StatusTask | None = None
):
    logger.info(f"Getting tasks with status: {status if status else 'All status tasks'}")
    tasks = service.get_tasks(status)
    return tasks