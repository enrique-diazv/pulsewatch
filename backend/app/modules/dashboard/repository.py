from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.database.models.monitor import Monitor
from app.database.models.monitor_check import MonitorCheck
from app.modules.incidents.enums import IncidentStatus
from app.modules.monitors.enums import MonitorStatus


@dataclass(frozen=True, slots=True)
class DashboardSummaryData:
    total_monitors: int
    operational_monitors: int
    down_monitors: int
    degraded_monitors: int
    active_incidents: int
    total_checks: int
    successful_checks: int
    average_response_time_ms: float | None


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summarize_for_user(
        self,
        user_id: UUID,
    ) -> DashboardSummaryData:
        monitor_summary = (
            select(
                func.count(Monitor.id).label(
                    "total_monitors",
                ),
                func.count(Monitor.id)
                .filter(Monitor.status == MonitorStatus.UP)
                .label("operational_monitors"),
                func.count(Monitor.id)
                .filter(Monitor.status == MonitorStatus.DOWN)
                .label("down_monitors"),
                func.count(Monitor.id)
                .filter(
                    Monitor.status == MonitorStatus.DEGRADED,
                )
                .label("degraded_monitors"),
            )
            .where(Monitor.user_id == user_id)
            .cte("monitor_summary")
        )

        incident_summary = (
            select(
                func.count(Incident.id).label(
                    "active_incidents",
                ),
            )
            .join(
                Monitor,
                Incident.monitor_id == Monitor.id,
            )
            .where(
                Monitor.user_id == user_id,
                Incident.status == IncidentStatus.OPEN,
            )
            .cte("incident_summary")
        )

        check_summary = (
            select(
                func.count(MonitorCheck.id).label(
                    "total_checks",
                ),
                func.count(MonitorCheck.id)
                .filter(MonitorCheck.success.is_(True))
                .label("successful_checks"),
                func.avg(
                    MonitorCheck.response_time_ms,
                ).label("average_response_time_ms"),
            )
            .join(
                Monitor,
                MonitorCheck.monitor_id == Monitor.id,
            )
            .where(Monitor.user_id == user_id)
            .cte("check_summary")
        )

        statement = (
            select(
                monitor_summary,
                incident_summary,
                check_summary,
            )
            .select_from(monitor_summary)
            .join(incident_summary, true())
            .join(check_summary, true())
        )
        result = await self.session.execute(statement)
        row = result.one()

        average_response_time = row.average_response_time_ms

        return DashboardSummaryData(
            total_monitors=row.total_monitors,
            operational_monitors=row.operational_monitors,
            down_monitors=row.down_monitors,
            degraded_monitors=row.degraded_monitors,
            active_incidents=row.active_incidents,
            total_checks=row.total_checks,
            successful_checks=row.successful_checks,
            average_response_time_ms=(
                float(average_response_time)
                if average_response_time is not None
                else None
            ),
        )
