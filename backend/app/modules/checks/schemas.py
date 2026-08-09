from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CheckQueuedResponse(BaseModel):
    task_id: str = Field(min_length=1)
    status: Literal["queued"] = "queued"


class MonitorCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monitor_id: UUID
    checked_at: datetime
    success: bool
    status_code: int | None
    response_time_ms: int
    error_type: str | None
    error_message: str | None
