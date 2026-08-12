from celery import Celery
from celery.schedules import crontab

from app.core.config import Settings, get_settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    resolved_settings = settings or get_settings()
    application = Celery(
        "pulsewatch",
        broker=str(resolved_settings.redis_url),
        include=(
            "app.workers.monitor_tasks",
            "app.workers.scheduler_tasks",
            "app.workers.notification_tasks",
            "app.workers.metric_tasks",
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
            "purge-expired-monitor-checks": {
                "task": ("app.workers.metric_tasks.purge_expired_monitor_checks"),
                "schedule": crontab(
                    hour=3,
                    minute=30,
                ),
                "options": {"queue": "monitoring"},
            },
            "aggregate-hourly-monitor-metrics": {
                "task": ("app.workers.metric_tasks.aggregate_hourly_metrics"),
                "schedule": crontab(minute=5),
                "options": {"queue": "monitoring"},
            },
            "dispatch-pending-notifications": {
                "task": (
                    "app.workers.notification_tasks.dispatch_pending_notifications"
                ),
                "schedule": float(
                    resolved_settings.notification_dispatch_interval_seconds
                ),
                "options": {"queue": "notifications"},
            },
            "schedule-due-monitors": {
                "task": ("app.workers.scheduler_tasks.schedule_due_monitors"),
                "schedule": float(resolved_settings.scheduler_poll_interval_seconds),
                "options": {"queue": "monitoring"},
            },
        },
    )

    return application


celery_app = create_celery_app()
