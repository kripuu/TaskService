from app.utils.config import Settings
import pytest

class TestSettings(Settings):
    POSTGRES_DB: str = "test_db"
    RABBITMQ_TASK_QUEUE: str = "test_task_queue"
    POSTGRES_USER: str = "test_user"
    POSTGRES_PASSWORD: str = "test_password"

@pytest.fixture
def test_settings():
    return TestSettings()