from fastapi import FastAPI
from api.tasks import task_router

app = FastAPI(title="Task Service")

app.include_router(task_router)