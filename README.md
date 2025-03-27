# TaskService

Сервис для управления задачами с использованием FastAPI, PostgreSQL и RabbitMQ.

## Функционал

- Создание задач через REST API и RabbitMQ
- Статусы задач (new_task → process_task → completed_task/error)
- Фильтрация задач по статусу
- Логирование всех операций

## Технологии

- Python 3.11
- FastAPI
- SQLAlchemy 2.0 (async)
- RabbitMQ (aio-pika)
- PostgreSQL
- Pydantic
- Tenacity (retry logic)

## Запуск

```bash
docker-compose up --build
```

## API Endpoints

- `POST /tasks` - Создать задачу
- `GET /tasks/{id}` - Получить задачу по ID
- `GET /tasks` - Список задач (с фильтром по статусу)

Документация: `http://localhost:8000/docs`

## Настройки

Переменные окружения:

- Настройки БД
- Параметры RabbitMQ
- Логирование
- Параметры воркера
