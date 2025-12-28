"""Celery application configuration."""

from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "signalflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.workers.tasks.ingest_tasks",
        "src.workers.tasks.strategy_tasks",
        "src.workers.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "fetch-qdii-data": {
        "task": "src.workers.tasks.ingest_tasks.fetch_qdii_data",
        "schedule": 300.0,  # Every 5 minutes
    },
    "run-strategies": {
        "task": "src.workers.tasks.strategy_tasks.run_all_strategies",
        "schedule": 300.0,  # Every 5 minutes
    },
    "process-deliveries": {
        "task": "src.workers.tasks.notification_tasks.process_pending_deliveries",
        "schedule": 60.0,  # Every minute
    },
}
