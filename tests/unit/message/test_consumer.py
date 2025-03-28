from typing import Any
import pytest
from unittest.mock import AsyncMock, patch
from aio_pika.abc import AbstractIncomingMessage

from app.message.consumer import process_single_message

@pytest.mark.asyncio
async def test_process_valid_message():
    mock_message = AsyncMock(spec=AbstractIncomingMessage)
    mock_message.body.decode.return_value = '{"task_id": 123}'
    mock_message.headers = {"retry_count": 0}
    
    with patch('app.message.consumer.process_task') as mock_process:
        await process_single_message(mock_message)
        
        mock_process.assert_awaited_once_with(123)
        mock_message.ack.assert_awaited_once()

@pytest.mark.asyncio
async def test_invalid_message_format():
    mock_message = AsyncMock()
    mock_message.body.decode.return_value = 'invalid_json'
    
    with patch('app.message.consumer.logger') as mock_logger:
        await process_single_message(mock_message)
        
        mock_logger.error.assert_called_with("JSON decode error: %s", Any)

@pytest.mark.asyncio
async def test_missing_task_id():
    mock_message = AsyncMock()
    mock_message.body.decode.return_value = '{"wrong_field": 123}'
    
    with patch('app.message.consumer.logger') as mock_logger:
        await process_single_message(mock_message)
        
        mock_logger.warning.assert_called_with("Invalid message format: missing task_id")