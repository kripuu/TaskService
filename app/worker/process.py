import asyncio
import random
from typing import Optional
from app.core.service.task import TaskService
from app.db import StatusTask, Task, get_session
from app.utils.config import settings
from app.utils.logging import logger
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from asyncio import CancelledError
from fastapi import HTTPException

async def _update_status(
    service: TaskService,
    task_id: int,
    status: StatusTask,
    message: str
) -> None:
    """Обновление статуса задачи"""
    logger.info(
        message,
        extra={
            "task_id": task_id,
            "status": status.value,
            "type": "STATUS_UPDATE"
        }
    )
    await service.update_task_status(task_id, status)

async def _simulate_processing(task_id: int) -> float:
    """Имитация обработки задачи"""
    processing_time = random.uniform(
        settings.TASK_MIN_PROCESS_TIME,
        settings.TASK_MAX_PROCESS_TIME
    )
    logger.info(
        "Task processing simulation",
        extra={
            "task_id": task_id,
            "processing_time": f"{processing_time:.2f}s",
            "type": "PROCESS_SIMULATION"
        }
    )
    await asyncio.sleep(processing_time)
    return processing_time

async def _should_fail() -> bool:
    """Определение вероятности ошибки"""
    return random.random() < settings.TASK_ERROR_PROBABILITY

async def _handle_error(
    service: TaskService,
    task_id: int,
    processing_time: float
) -> None:
    """Обработка сценария ошибки"""
    error_msg = f"Processing failed after {processing_time:.2f}s"
    logger.warning(
        "Task processing failed",
        extra={
            "task_id": task_id,
            "error": error_msg,
            "processing_time": processing_time,
            "type": "PROCESS_FAILURE"
        }
    )
    await service.update_task_status(
        task_id,
        StatusTask.ERROR,
        error_message=error_msg
    )

async def _handle_success(
    service: TaskService,
    task_id: int,
    processing_time: float
) -> None:
    """Обработка успешного завершения"""
    result_msg = f"Processed in {processing_time:.2f}s"
    logger.info(
        "Task completed successfully",
        extra={
            "task_id": task_id,
            "result": result_msg,
            "processing_time": processing_time,
            "type": "PROCESS_SUCCESS"
        }
    )
    await service.update_task_status(
        task_id,
        StatusTask.COMPLETED_TASK,
        result=result_msg
    )

async def _handle_processing_error(
    service: TaskService,
    task: Optional[Task],
    error: Exception
) -> None:
    """Обработка непредвиденных ошибок"""
    error_msg = f"Critical error: {str(error)}"
    logger.error(
        "Task processing failure",
        extra={
            "task_id": task.id if task else "unknown",
            "error": error_msg,
            "type": "CRITICAL_ERROR"
        },
        exc_info=True
    )
    
    if task:
        await service.update_task_status(
            task.id,
            StatusTask.ERROR,
            error_message=error_msg
        )

async def _handle_cancell(service: TaskService, task_id: int):
    """Отмена задачи"""
    logger.warning("Processing cancelled", extra={"task_id": task_id})
    await service.update_task_status(
        task_id,
        StatusTask.ERROR,
        error_message="Processing cancelled"
    )

def log_retry_attempt(retry_state):
    """Логирование повторных попыток"""
    logger.warning(
        "Retrying processing",
        extra={
            "task_id": retry_state.args[0],
            "attempt": retry_state.attempt_number,
            "exception": str(retry_state.outcome.exception())
        }
    )

@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=log_retry_attempt
)
async def process_task(task_id: int) -> None:
    """Обработка задачи"""
    try:
        async with get_session() as session:
            service = TaskService(session)
            try:
                task = await service.get_task(task_id)
            except HTTPException as e:
                if e.status_code == 404:
                    logger.error("Task not found, skipping", extra={"task_id": task_id})
                    return
                raise

            # Проверяем уже обработанные
            if task.status not in [StatusTask.NEW_TASK, StatusTask.ERROR]:
                logger.warning(
                    "Task in non-processable status",
                    extra={"task_id": task_id, "status": task.status.value}
                )
                return

            await _update_status(service, task_id, StatusTask.PROCESS_TASK, "Processing started")
            
            try:
                processing_time = await _simulate_processing(task_id)
            except CancelledError:
                await _handle_cancell(service, task_id)
                raise

            if await _should_fail():
                await _handle_error(service, task_id, processing_time)
            else:
                await _handle_success(service, task_id, processing_time)

    except CancelledError:
        logger.warning("Task processing cancelled", extra={"task_id": task_id})
        raise
    except Exception as e:
        await _handle_processing_error(service, task, e)


async def main():
    from app.message.consumer import consume_tasks
    await consume_tasks()

if __name__ == "__main__":
    asyncio.run(main())