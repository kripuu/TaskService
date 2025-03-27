import logging
import sys
from pydantic import BaseModel
from app.utils.config import settings
from logging.config import dictConfig

class LogConfig(BaseModel):
    """Конфигурация логирования"""
    LOGGER_NAME: str = "task_service"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(name)s | %(message)s"
    LOG_LEVEL: str = "INFO"

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s"
        }
    }
    handlers: dict = {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "filters": ["sensitive_data"]
        },
        "file": {
            "formatter": "json",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    }
    filters: dict = {
        "sensitive_data": {
            "()": "app.utils.logging.SensitiveDataFilter"
        }
    }
    loggers: dict = {
        LOGGER_NAME: {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False
        }
    }

def setup_logging():
    config = LogConfig()
    config.LOG_LEVEL = settings.LOG_LEVEL
    dictConfig(config.model_dump())

setup_logging()
logger = logging.getLogger("task_service")