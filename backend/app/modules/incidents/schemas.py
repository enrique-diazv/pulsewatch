from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.incidents.enums import IncidentStatus


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    monitor_id: UUID
    started_at: datetime
    resolved_at: datetime | None
    status: IncidentStatus
    failure_reason: str
    initial_check_id: int
    recovery_check_id: int | None
