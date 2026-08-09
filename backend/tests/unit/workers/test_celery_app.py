from app.core.config import Settings
from app.workers.celery_app import create_celery_app


def test_create_celery_app_uses_secure_worker_defaults() -> None:
    settings = Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key="test-jwt-secret-key-with-at-least-32-characters",
        redis_url="redis://127.0.0.1:6379/3",
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
