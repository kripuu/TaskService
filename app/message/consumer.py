import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from app.utils.config import settings
from app.utils.logging import logger
from app.worker.process import process_task
from tenacity import retry, stop_after_attempt, wait_random_exponential

async def consume_tasks():
    connection = None
    try:
        connection = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD,
        )
        
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            
            queue = await channel.declare_queue(
                settings.RABBITMQ_TASK_QUEUE,
                durable=True,
                arguments={
                    "x-queue-type": "quorum",
                    "x-dead-letter-exchange": "dead_letter_exchange"
                }
            )
            
            logger.info("Consumer started for queue: %s", queue.name)
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        await process_single_message(message)
                    except Exception as e:
                        logger.error("Message processing failed: %s", e)
                        await message.reject(requeue=False)

    except Exception as e:
        logger.critical("Consumer crashed: %s", e)
        if connection:
            await connection.close()
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10)
)
async def process_single_message(message: AbstractIncomingMessage):
    """Обработка с повторными попытками"""
    async with message.process():
        try:
            body = message.body.decode()
            data = json.loads(body)
            task_id = data.get("task_id")
            
            if not task_id:
                logger.warning("Invalid message format: missing task_id")
                return
                
            logger.info(
                "Processing task message",
                extra={
                    "task_id": task_id,
                    "headers": message.headers
                }
            )
            
            await process_task(task_id)
            
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
        except KeyError as e:
            logger.error("Missing required field: %s", str(e))
        except Exception as e:
            logger.error(
                "Task processing failed: %s",
                str(e),
                exc_info=True
            )
            await message.reject(requeue=False)
            raise