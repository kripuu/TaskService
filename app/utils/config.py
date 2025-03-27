from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # БАЗЫ
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: PostgresDsn | None = None

    @model_validator(mode='before')
    def assemble_db_connection(cls, values: dict):
        if not values.get("DATABASE_URL"):
            values["DATABASE_URL"] = PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                path=f"/{values.get('POSTGRES_DB') or ''}",
            )
        return values
    
    # БРОКЕР
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_TASK_QUEUE: str = "task_queue"

    #ВОРКЕР
    TASK_MIN_PROCESS_TIME: float = 5.0    # Минимальное время обработки в секундах
    TASK_MAX_PROCESS_TIME: float = 10.0   # Максимальное время обработки в секундах
    TASK_ERROR_PROBABILITY: float = 0.2   # Вероятность ошибки
    TASK_MAX_RETRIES: int = 3             # Максимальное количество попыток повторной обр-ки
    TASK_RETRY_DELAY: int = 40            # Задержка между повторами в секундах
    WORKER_MAX_CONCURRENT_TASKS: int = 10 # Максимальное число параллельных задач
    WORKER_PREFETCH_COUNT: int = 5        # Количество предзагружаемых сообщений

    #ЛОГЕР
    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()