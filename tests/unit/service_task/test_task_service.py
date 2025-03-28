import pytest
from unittest.mock import AsyncMock
from app.core.service.task import TaskService
from app.db import Task, StatusTask
from app.core.schemas.task import TaskCreate, TaskUpdate, TaskRead
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from fastapi import HTTPException

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_create_task_success(mock_session):
    service = TaskService(mock_session)
    task_data = TaskCreate(title="Test", description="test")
    
    result = await service.create_task(task_data)
    
    assert isinstance(result, TaskRead)
    assert result.status == StatusTask.NEW_TASK
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_task_found(mock_session):
    mock_task = Task(id=1, title="Test")
    mock_session.get.return_value = mock_task
    service = TaskService(mock_session)
    
    result = await service.get_task(1)
    
    assert isinstance(result, TaskRead)
    assert result.id == 1
    mock_session.get.assert_awaited_once_with(Task, 1)

@pytest.mark.asyncio
async def test_get_task_not_found(mock_session):
    mock_session.get.return_value = None
    service = TaskService(mock_session)
    
    with pytest.raises(HTTPException) as exc_info:
        await service.get_task(999)
    
    assert exc_info.value.status_code == 404
    assert "Task with id 999 not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_update_task_status_success(mock_session):
    original_task = Task(
        id=1,
        title="Test",
        status=StatusTask.NEW_TASK,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_session.get.return_value = original_task
    service = TaskService(mock_session)
    
    result = await service.update_task_status(
        task_id=1,
        status=StatusTask.COMPLETED_TASK,
        result="Success"
    )
    
    assert isinstance(result, TaskRead)
    assert result.status == StatusTask.COMPLETED_TASK
    assert result.result == "Success"
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_tasks_with_filter(mock_session):
    mock_tasks = [
        Task(id=1, title="Test1", status=StatusTask.NEW_TASK),
        Task(id=2, title="Test2", status=StatusTask.NEW_TASK)
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = mock_tasks
    service = TaskService(mock_session)
    
    results = await service.get_tasks(status=StatusTask.NEW_TASK)
    
    assert len(results) == 2
    assert all(isinstance(task, TaskRead) for task in results)
    assert all(task.status == StatusTask.NEW_TASK for task in results)

@pytest.mark.asyncio
async def test_update_task_partial_data(mock_session):
    original_task = Task(
        id=1,
        title="Original",
        description="Old",
        status=StatusTask.NEW_TASK
    )
    mock_session.get.return_value = original_task
    service = TaskService(mock_session)
    
    update_data = TaskUpdate(title="New Title")
    result = await service.update_task(1, update_data)
    
    assert isinstance(result, TaskRead)
    assert result.title == "New Title"
    assert result.description == "Old"

@pytest.mark.asyncio
async def test_update_task_status_with_error(mock_session):
    task = Task(id=1, status=StatusTask.NEW_TASK)
    mock_session.get.return_value = task
    service = TaskService(mock_session)
    
    result = await service.update_task_status(
        task_id=1,
        status=StatusTask.ERROR,
        error_message="Failure"
    )
    
    assert result.status == StatusTask.ERROR
    assert result.error_message == "Failure"
    assert result.result is None

@pytest.mark.asyncio
async def test_update_task_not_found(mock_session):
    mock_session.get.return_value = None
    service = TaskService(mock_session)
    
    with pytest.raises(HTTPException) as exc_info:
        await service.update_task(999, TaskUpdate(title="New"))
    
    assert exc_info.value.status_code == 404
    assert "Task with id 999 not found" in str(exc_info.value.detail)