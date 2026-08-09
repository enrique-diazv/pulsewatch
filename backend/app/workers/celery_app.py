from celery import Celery

from app.core.config import Settings, get_settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    resolved_settings = settings or get_settings()
    application = Celery(
        "pulsewatch",
        broker=str(resolved_settings.redis_url),
        include=(
            "app.workers.monitor_tasks",
            "app.workers.scheduler_tasks",
        ),
    )
    application.conf.update(
        accept_content=("json",),
        broker_connection_retry_on_startup=True,
        enable_utc=True,
        task_acks_late=True,
        task_default_queue="monitoring",
        task_ignore_result=True,
        task_reject_on_worker_lost=True,
        task_serializer="json",
        timezone="UTC",
        worker_prefetch_multiplier=1,
        beat_schedule={
            "schedule-due-monitors": {
                "task": ("app.workers.scheduler_tasks.schedule_due_monitors"),
                "schedule": float(resolved_settings.scheduler_poll_interval_seconds),
                "options": {"queue": "monitoring"},
            },
        },
    )

    return application


celery_app = create_celery_app()
