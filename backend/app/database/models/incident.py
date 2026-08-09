from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.modules.incidents.enums import IncidentStatus


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            """
            (
                status = 'OPEN'
                AND resolved_at IS NULL
                AND recovery_check_id IS NULL
            )
            OR
            (
                status = 'RESOLVED'
                AND resolved_at IS NOT NULL
                AND recovery_check_id IS NOT NULL
            )
            """,
            name="incident_resolution_consistency",
        ),
        Index(
            "ix_incidents_monitor_id_started_at",
            "monitor_id",
            "started_at",
        ),
        Index(
            "uq_incidents_open_monitor_id",
            "monitor_id",
            unique=True,
            postgresql_where=text("status = 'OPEN'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    monitor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(
            IncidentStatus,
            name="incident_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        default=IncidentStatus.OPEN,
        server_default=IncidentStatus.OPEN.value,
        nullable=False,
    )
    failure_reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    initial_check_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("monitor_checks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recovery_check_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("monitor_checks.id", ondelete="RESTRICT"),
        nullable=True,
    )
