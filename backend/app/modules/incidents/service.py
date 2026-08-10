from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.database.models.monitor import Monitor
from app.database.models.monitor_check import MonitorCheck
from app.database.models.notification import Notification
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.exceptions import IncidentNotFoundError
from app.modules.incidents.repository import IncidentRepository
from app.modules.monitors.state import evaluate_monitor_state
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.repository import (
    NotificationRepository,
)


class IncidentDetectionService:
    def __init__(
        self,
        repository: IncidentRepository,
        notification_repository: NotificationRepository,
    ) -> None:
        self.repository = repository
        self.notification_repository = notification_repository

    async def process_check(
        self,
        monitor: Monitor,
        monitor_check: MonitorCheck,
    ) -> Incident | None:
        state_update = evaluate_monitor_state(
            current_status=monitor.status,
            check_succeeded=monitor_check.success,
            consecutive_failures=monitor.consecutive_failures,
            consecutive_successes=monitor.consecutive_successes,
            failure_threshold=monitor.failure_threshold,
            recovery_threshold=monitor.recovery_threshold,
        )

        monitor.status = state_update.status
        monitor.consecutive_failures = state_update.consecutive_failures
        monitor.consecutive_successes = state_update.consecutive_successes
        monitor.last_checked_at = monitor_check.checked_at

        if state_update.went_down:
            incident = Incident(
                monitor_id=monitor.id,
                started_at=monitor_check.checked_at,
                failure_reason=(
                    monitor_check.error_message
                    or monitor_check.error_type
                    or "Monitor check failed"
                ),
                initial_check_id=monitor_check.id,
            )
            incident = await self.repository.add(incident)
            await self.notification_repository.add(
                Notification(
                    user_id=monitor.user_id,
                    incident_id=incident.id,
                    type=NotificationType.INCIDENT_OPENED,
                )
            )

            return incident

        if state_update.recovered:
            incident = await self.repository.get_open_for_update(
                monitor.id,
            )

            if incident is None:
                return None

            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = monitor_check.checked_at
            incident.recovery_check_id = monitor_check.id
            await self.notification_repository.add(
                Notification(
                    user_id=monitor.user_id,
                    incident_id=incident.id,
                    type=NotificationType.INCIDENT_RESOLVED,
                )
            )
            return incident

        return None


class IncidentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: IncidentRepository | None = None,
    ) -> None:
        self.repository = repository or IncidentRepository(session)

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: IncidentStatus | None = None,
    ) -> list[Incident]:
        return await self.repository.list_for_user(
            user_id,
            status=status,
        )

    async def get_for_user(
        self,
        incident_id: UUID,
        user_id: UUID,
    ) -> Incident:
        incident = await self.repository.get_for_user(
            incident_id,
            user_id,
        )

        if incident is None:
            raise IncidentNotFoundError

        return incident
