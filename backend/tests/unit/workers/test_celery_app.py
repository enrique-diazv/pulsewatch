from app.core.config import Settings
from app.workers.celery_app import create_celery_app


def test_create_celery_app_uses_secure_worker_defaults() -> None:
    settings = Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key="test-jwt-secret-key-with-at-least-32-characters",
        redis_url="redis://127.0.0.1:6379/3",
        scheduler_poll_interval_seconds=7,
        notification_dispatch_interval_seconds=11,
    )

    application = create_celery_app(settings)

    assert application.main == "pulsewatch"
    assert application.conf.broker_url == "redis://127.0.0.1:6379/3"
    assert application.conf.accept_content == ("json",)
    assert application.conf.task_serializer == "json"
    assert application.conf.task_ignore_result is True
    assert application.conf.task_acks_late is True
    assert application.conf.task_reject_on_worker_lost is True
    assert application.conf.worker_prefetch_multiplier == 1
    assert application.conf.task_default_queue == "monitoring"
    assert application.conf.enable_utc is True
    assert application.conf.timezone == "UTC"

    assert application.conf.include == (
        "app.workers.monitor_tasks",
        "app.workers.scheduler_tasks",
        "app.workers.notification_tasks",
        "app.workers.metric_tasks",
    )

    schedule = application.conf.beat_schedule["schedule-due-monitors"]
    notification_schedule = application.conf.beat_schedule[
        "dispatch-pending-notifications"
    ]
    metric_schedule = application.conf.beat_schedule["aggregate-hourly-monitor-metrics"]
    retention_schedule = application.conf.beat_schedule["purge-expired-monitor-checks"]

    assert notification_schedule["task"] == (
        "app.workers.notification_tasks.dispatch_pending_notifications"
    )
    assert notification_schedule["schedule"] == 11.0
    assert notification_schedule["options"] == {"queue": "notifications"}
    assert schedule["task"] == ("app.workers.scheduler_tasks.schedule_due_monitors")
    assert schedule["schedule"] == 7.0
    assert schedule["options"] == {"queue": "monitoring"}
    assert metric_schedule["task"] == (
        "app.workers.metric_tasks.aggregate_hourly_metrics"
    )
    assert set(metric_schedule["schedule"].minute) == {5}
    assert metric_schedule["options"] == {
        "queue": "monitoring",
    }
    assert retention_schedule["task"] == (
        "app.workers.metric_tasks.purge_expired_monitor_checks"
    )
    assert set(
        retention_schedule["schedule"].hour,
    ) == {3}
    assert set(
        retention_schedule["schedule"].minute,
    ) == {30}
    assert retention_schedule["options"] == {
        "queue": "monitoring",
    }
