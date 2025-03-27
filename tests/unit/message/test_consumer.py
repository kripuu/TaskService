import pytest
from unittest.mock import AsyncMock, patch
from app.message.producer import publish_task
from aio_pika.exceptions import AMQPConnectionError

@pytest.mark.asyncio
async def test_publish_task_success():
    with patch('app.message.producer.get_rabbitmq_connection') as mock_conn:
        mock_channel = AsyncMock()
        mock_conn.return_value.__aenter__.return_value.channel.return_value = mock_channel
        
        await publish_task(123)
        
        mock_channel.declare_queue.assert_awaited_once()
        mock_channel.default_exchange.publish.assert_awaited_once()
        
@pytest.mark.asyncio
async def test_publish_task_retry_on_connection_error():
    with patch('app.message.producer.get_rabbitmq_connection', 
              side_effect=AMQPConnectionError) as mock_conn:
        with pytest.raises(AMQPConnectionError):
            await publish_task(123)
        assert mock_conn.call_count == 3

@pytest.mark.asyncio
async def test_message_properties():
    with patch('app.message.producer.get_rabbitmq_connection') as mock_conn:
        mock_channel = AsyncMock()
        mock_conn.return_value.__aenter__.return_value.channel.return_value = mock_channel
        
        await publish_task(123)
        
        message = mock_channel.default_exchange.publish.call_args[0][0]
        assert message.delivery_mode == 2  # PERSISTENT
        assert message.headers["service"] == "task-manager"