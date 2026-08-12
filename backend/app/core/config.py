from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    app_name: str = "PulseWatch API"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"
    cors_allowed_origins: tuple[str, ...] = ("http://localhost:5173",)
    database_host: str = "127.0.0.1"
    database_port: int = 5432
    database_name: str = "pulsewatch"
    database_user: str = "pulsewatch_app"
    database_password: SecretStr
    redis_url: RedisDsn = RedisDsn("redis://127.0.0.1:6379/0")
    dashboard_cache_ttl_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
    )
    raw_check_retention_days: int = Field(
        default=30,
        ge=7,
        le=365,
    )
    retention_batch_size: int = Field(
        default=10_000,
        ge=100,
        le=100_000,
    )
    manual_check_cooldown_seconds: int = Field(
        default=10,
        ge=5,
        le=300,
    )
    scheduler_poll_interval_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
    )
    scheduler_batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
    )
    notification_dispatch_interval_seconds: int = Field(
        default=15,
        ge=5,
        le=300,
    )
    notification_batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
    )
    notification_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
    )
    email_delivery_mode: Literal["log", "smtp"] = "log"
    email_from_address: str = "alerts@pulsewatch.local"
    smtp_host: str = "127.0.0.1"
    smtp_port: int = Field(
        default=1025,
        ge=1,
        le=65535,
    )
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool = False
    smtp_start_tls: bool = False
    jwt_secret_key: SecretStr = Field(min_length=32)
    access_token_expire_minutes: int = Field(
        default=15,
        ge=1,
        le=60,
    )
    refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        le=90,
    )
    realtime_ticket_ttl_seconds: int = Field(
        default=30,
        ge=10,
        le=120,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
