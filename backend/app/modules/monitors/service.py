from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.modules.monitors.enums import MonitorStatus
from app.modules.monitors.exceptions import MonitorNotFoundError
from app.modules.monitors.repository import MonitorRepository
from app.modules.monitors.schemas import MonitorCreate, MonitorUpdate


class MonitorService:
    def __init__(
        self,
        session: AsyncSession,
        repository: MonitorRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or MonitorRepository(session)

    async def create(
        self,
        user_id: UUID,
        request: MonitorCreate,
        *,
        now: datetime | None = None,
    ) -> Monitor:
        created_at = now or datetime.now(UTC)
        monitor = Monitor(
            user_id=user_id,
            name=request.name,
            url=str(request.url),
            method=request.method,
            interval_seconds=request.interval_seconds,
            timeout_seconds=request.timeout_seconds,
            expected_status=request.expected_status,
            status=MonitorStatus.UNKNOWN,
            failure_threshold=request.failure_threshold,
            recovery_threshold=request.recovery_threshold,
            consecutive_failures=0,
            consecutive_successes=0,
            is_active=True,
            next_check_at=created_at,
        )

        await self.repository.add(monitor)
        await self.session.commit()
        await self.session.refresh(monitor)

        return monitor

    async def list_for_user(self, user_id: UUID) -> list[Monitor]:
        return await self.repository.list_for_user(user_id)

    async def get_for_user(
        self,
        monitor_id: UUID,
        user_id: UUID,
    ) -> Monitor:
        monitor = await self.repository.get_for_user(
            monitor_id,
            user_id,
        )

        if monitor is None:
            raise MonitorNotFoundError

        return monitor

    async def update(
        self,
        monitor_id: UUID,
        user_id: UUID,
        request: MonitorUpdate,
        *,
        now: datetime | None = None,
    ) -> Monitor:
        monitor = await self.get_for_user(monitor_id, user_id)
        changes = request.model_dump(exclude_none=True)

        if "url" in changes:
            changes["url"] = str(changes["url"])

        for field, value in changes.items():
            setattr(monitor, field, value)

        if monitor.is_active:
            monitor.next_check_at = now or datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(monitor)

        return monitor

    async def delete(
        self,
        monitor_id: UUID,
        user_id: UUID,
    ) -> None:
        monitor = await self.get_for_user(monitor_id, user_id)

        await self.repository.delete(monitor)
        await self.session.commit()

    async def pause(
        self,
        monitor_id: UUID,
        user_id: UUID,
    ) -> Monitor:
        monitor = await self.get_for_user(monitor_id, user_id)
        monitor.is_active = False
        monitor.status = MonitorStatus.PAUSED

        await self.session.commit()
        await self.session.refresh(monitor)

        return monitor

    async def resume(
        self,
        monitor_id: UUID,
        user_id: UUID,
        *,
        now: datetime | None = None,
    ) -> Monitor:
        monitor = await self.get_for_user(monitor_id, user_id)
        monitor.is_active = True
        monitor.status = MonitorStatus.UNKNOWN
        monitor.next_check_at = now or datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(monitor)

        return monitor
