from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_monitors: int = Field(ge=0)
    operational_monitors: int = Field(ge=0)
    down_monitors: int = Field(ge=0)
    degraded_monitors: int = Field(ge=0)
    active_incidents: int = Field(ge=0)
    total_checks: int = Field(ge=0)
    successful_checks: int = Field(ge=0)
    overall_uptime_percentage: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    average_response_time_ms: float | None = Field(
        default=None,
        ge=0,
    )
