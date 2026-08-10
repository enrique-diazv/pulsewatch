from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.models.incident import Incident
from app.database.models.monitor import Monitor
from app.database.models.monitor_check import MonitorCheck
from app.modules.checks.engine import HttpCheckEngine
from app.modules.checks.repository import MonitorCheckRepository
from app.modules.checks.schemas import MetricsRange, MonitorMetricsResponse
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.service import IncidentDetectionService
from app.modules.notifications.repository import (
    NotificationRepository,
)
from app.modules.realtime.events import (
    RealtimeEvent,
    RealtimeEventType,
    RealtimePublisher,
)

METRICS_RANGE_DURATIONS: dict[MetricsRange, timedelta] = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}
logger = get_logger(__name__)


def utc_now() -> datetime:
    return datetime.now(UTC)


class CheckExecutionService:
    def __init__(
        self,
        session: AsyncSession,
        engine: HttpCheckEngine,
        repository: MonitorCheckRepository | None = None,
        incident_service: IncidentDetectionService | None = None,
        realtime_publisher: RealtimePublisher | None = None,
    ) -> None:
        self.session = session
        self.engine = engine
        self.repository = repository or MonitorCheckRepository(session)
        self.incident_service = incident_service or IncidentDetectionService(
            IncidentRepository(session),
            NotificationRepository(session),
        )
        self.realtime_publisher = realtime_publisher

    async def execute(self, monitor: Monitor) -> MonitorCheck:
        result = await self.engine.execute(
            url=monitor.url,
            timeout_seconds=monitor.timeout_seconds,
            expected_status=monitor.expected_status,
        )
        await self.session.refresh(
            monitor,
            with_for_update=True,
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
        incident = await self.incident_service.process_check(
            monitor,
            monitor_check,
        )
        await self.session.commit()
        await self.session.refresh(monitor_check)

        await self._publish_events(
            monitor,
            monitor_check,
            incident,
        )

        return monitor_check

    async def _publish_events(
        self,
        monitor: Monitor,
        monitor_check: MonitorCheck,
        incident: Incident | None,
    ) -> None:
        if self.realtime_publisher is None:
            return

        events = [
            RealtimeEvent(
                type=RealtimeEventType.MONITOR_UPDATED,
                monitor_id=monitor.id,
                monitor_status=monitor.status,
                check_id=monitor_check.id,
            )
        ]

        if incident is not None:
            incident_event_type = (
                RealtimeEventType.INCIDENT_RESOLVED
                if incident.status == IncidentStatus.RESOLVED
                else RealtimeEventType.INCIDENT_OPENED
            )
            events.append(
                RealtimeEvent(
                    type=incident_event_type,
                    monitor_id=monitor.id,
                    monitor_status=monitor.status,
                    check_id=monitor_check.id,
                    incident_id=incident.id,
                )
            )

        for event in events:
            try:
                await self.realtime_publisher.publish(
                    monitor.user_id,
                    event,
                )
            except Exception:
                logger.exception(
                    "realtime_event_publish_failed",
                    extra={
                        "user_id": str(monitor.user_id),
                        "monitor_id": str(monitor.id),
                        "check_id": monitor_check.id,
                        "realtime_event_type": event.type,
                    },
                )


class MonitorMetricsService:
    def __init__(
        self,
        session: AsyncSession,
        repository: MonitorCheckRepository | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.repository = repository or MonitorCheckRepository(session)
        self.clock = clock

    async def summarize(
        self,
        monitor_id: UUID,
        metrics_range: MetricsRange,
    ) -> MonitorMetricsResponse:
        to_timestamp = self.clock()
        from_timestamp = to_timestamp - METRICS_RANGE_DURATIONS[metrics_range]
        summary = await self.repository.summarize_for_monitor(
            monitor_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
        )
        failed_checks = summary.total_checks - summary.successful_checks

        uptime_percentage = None
        if summary.total_checks > 0:
            uptime_percentage = round(
                (summary.successful_checks / summary.total_checks) * 100,
                2,
            )

        average_response_time = (
            round(summary.average_response_time_ms, 2)
            if summary.average_response_time_ms is not None
            else None
        )

        return MonitorMetricsResponse(
            range=metrics_range,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            total_checks=summary.total_checks,
            successful_checks=summary.successful_checks,
            failed_checks=failed_checks,
            uptime_percentage=uptime_percentage,
            average_response_time_ms=average_response_time,
        )
