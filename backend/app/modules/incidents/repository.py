from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.database.models.monitor import Monitor
from app.modules.incidents.enums import IncidentStatus


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.flush()

        return incident

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        status: IncidentStatus | None = None,
    ) -> list[Incident]:
        statement = (
            select(Incident)
            .join(
                Monitor,
                Incident.monitor_id == Monitor.id,
            )
            .where(Monitor.user_id == user_id)
        )

        if status is not None:
            statement = statement.where(
                Incident.status == status,
            )

        statement = statement.order_by(
            Incident.started_at.desc(),
            Incident.id.desc(),
        )
        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_for_user(
        self,
        incident_id: UUID,
        user_id: UUID,
    ) -> Incident | None:
        statement = (
            select(Incident)
            .join(
                Monitor,
                Incident.monitor_id == Monitor.id,
            )
            .where(
                Incident.id == incident_id,
                Monitor.user_id == user_id,
            )
        )
        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_open_for_update(
        self,
        monitor_id: UUID,
    ) -> Incident | None:
        statement = (
            select(Incident)
            .where(
                Incident.monitor_id == monitor_id,
                Incident.status == IncidentStatus.OPEN,
            )
            .with_for_update()
        )
        result = await self.session.execute(statement)

        return result.scalar_one_or_none()
