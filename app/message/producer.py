import json
import aio_pika
from aio_pika.abc import AbstractChannel
from app.utils.config import settings
from app.utils.logging import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aio_pika.exceptions import AMQPConnectionError

async def get_rabbitmq_connection():
    """Соединение с RabbitMQ"""
    return await aio_pika.connect_robust(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        login=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD,
    )

async def get_rabbitmq_channel() -> AbstractChannel:
    """Возвращает канал с предварительно объявленной очередью"""
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    await channel.declare_queue(
        settings.RABBITMQ_TASK_QUEUE,
        durable=True,
        arguments={
            "x-queue-type": "quorum"
        }
    )
    return channel

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(AMQPConnectionError)
)
async def publish_task(task_id: int) -> None:
    """Публикует задачу в очередь"""
    try:
        connection = await get_rabbitmq_connection()
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(
                settings.RABBITMQ_TASK_QUEUE,
                durable=True,
                arguments={
                    "x-queue-type": "quorum",
                    "x-dead-letter-exchange": "dead_letter_exchange"
                }
            )
            
            message = aio_pika.Message(
                body=json.dumps({"task_id": task_id}).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "retry_count": 0,
                    "service": "task-manager",
                    "version": "1.0"
                }
            )
            
            await channel.default_exchange.publish(
                message,
                routing_key=settings.RABBITMQ_TASK_QUEUE,
                mandatory=True
            )
            logger.info("Task published", extra={"task_id": task_id})

    except AMQPConnectionError as e:
        logger.error("Connection failed after retries: %s", e)
        raise