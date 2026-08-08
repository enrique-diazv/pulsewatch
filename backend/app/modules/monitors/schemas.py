from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    UrlConstraints,
    model_validator,
)

from app.modules.monitors.enums import HttpMethod, MonitorStatus

MonitorUrl = Annotated[
    AnyHttpUrl,
    UrlConstraints(
        max_length=2048,
        allowed_schemes=["http", "https"],
    ),
]


class MonitorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    url: MonitorUrl
    method: HttpMethod = HttpMethod.GET
    interval_seconds: int = Field(default=60, ge=30, le=86400)
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    expected_status: int = Field(default=200, ge=100, le=599)
    failure_threshold: int = Field(default=3, ge=1, le=10)
    recovery_threshold: int = Field(default=2, ge=1, le=10)


class MonitorUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    url: MonitorUrl | None = None
    method: HttpMethod | None = None
    interval_seconds: int | None = Field(default=None, ge=30, le=86400)
    timeout_seconds: int | None = Field(default=None, ge=1, le=60)
    expected_status: int | None = Field(default=None, ge=100, le=599)
    failure_threshold: int | None = Field(default=None, ge=1, le=10)
    recovery_threshold: int | None = Field(default=None, ge=1, le=10)

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> "MonitorUpdate":
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("At least one field must be provided")

        return self


class MonitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    method: HttpMethod
    interval_seconds: int
    timeout_seconds: int
    expected_status: int
    status: MonitorStatus
    failure_threshold: int
    recovery_threshold: int
    is_active: bool
    last_checked_at: datetime | None
    next_check_at: datetime
    created_at: datetime
    updated_at: datetime
