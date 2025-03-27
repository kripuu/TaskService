from datetime import datetime
from pydantic import BaseModel, Field
from app.db import StatusTask

class TaskBase(BaseModel):
    title: str = Field(..., max_length=90)
    description: str | None = Field(None, max_length=500)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: str | None = Field(..., max_length=90)
    description: str | None = Field(None, max_length=500)
    status: StatusTask | None = None
    result: str | None = Field(None, max_length=500)
    error_message: str | None = None

class TaskRead(TaskBase):
    id: int
    status: StatusTask
    created_at: datetime
    updated_at: datetime
    result: str | None = None
    error_message: str | None = None
