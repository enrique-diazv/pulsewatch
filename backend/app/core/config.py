from functools import lru_cache
from pathlib import Path
from typing import Literal

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
