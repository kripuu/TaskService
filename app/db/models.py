from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass

class StatusTask(StrEnum):
    NEW_TASK = "new_task"
    PROCESS_TASK = "process_task"
    COMPLETED_TASK = "completed_task"
    ERROR = "error"

class Task(Base):
    """Модель таблицы задач"""
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(90))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[StatusTask] = mapped_column(Enum(StatusTask), default=StatusTask.NEW_TASK)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )
    result: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)