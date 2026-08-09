from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.database.models.monitor_check import MonitorCheck
from app.modules.checks.engine import HttpCheckEngine
from app.modules.checks.repository import MonitorCheckRepository
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.service import IncidentDetectionService


class CheckExecutionService:
    def __init__(
        self,
        session: AsyncSession,
        engine: HttpCheckEngine,
        repository: MonitorCheckRepository | None = None,
        incident_service: IncidentDetectionService | None = None,
    ) -> None:
        self.session = session
        self.engine = engine
        self.repository = repository or MonitorCheckRepository(session)
        self.incident_service = incident_service or IncidentDetectionService(
            IncidentRepository(session)
        )

    async def execute(self, monitor: Monitor) -> MonitorCheck:
        result = await self.engine.execute(
            url=monitor.url,
            timeout_seconds=monitor.timeout_seconds,
            expected_status=monitor.expected_status,
        )
        monitor_check = MonitorCheck(
            monitor_id=monitor.id,
            success=result.success,
            status_code=result.status_code,
            response_time_ms=result.response_time_ms,
            error_type=(
                result.error_type.value if result.error_type is not None else None
            ),
            error_message=result.error_message,
        )

        await self.repository.add(monitor_check)
        await self.incident_service.process_check(
            monitor,
            monitor_check,
        )
        await self.session.commit()
        await self.session.refresh(monitor_check)

        return monitor_check
