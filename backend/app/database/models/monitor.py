from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.modules.monitors.enums import HttpMethod, MonitorStatus


class Monitor(Base):
    __tablename__ = "monitors"
    __table_args__ = (
        CheckConstraint(
            "interval_seconds BETWEEN 30 AND 86400",
            name="interval_seconds_range",
        ),
        CheckConstraint(
            "timeout_seconds BETWEEN 1 AND 60",
            name="timeout_seconds_range",
        ),
        CheckConstraint(
            "expected_status BETWEEN 100 AND 599",
            name="expected_status_range",
        ),
        CheckConstraint(
            "failure_threshold BETWEEN 1 AND 10",
            name="failure_threshold_range",
        ),
        CheckConstraint(
            "recovery_threshold BETWEEN 1 AND 10",
            name="recovery_threshold_range",
        ),
        CheckConstraint(
            "consecutive_failures >= 0",
            name="consecutive_failures_nonnegative",
        ),
        CheckConstraint(
            "consecutive_successes >= 0",
            name="consecutive_successes_nonnegative",
        ),
        Index(
            "ix_monitors_user_id_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_monitors_is_active_next_check_at",
            "is_active",
            "next_check_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    method: Mapped[HttpMethod] = mapped_column(
        Enum(
            HttpMethod,
            name="monitor_http_method",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        default=HttpMethod.GET,
        server_default=HttpMethod.GET.value,
        nullable=False,
    )
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_status: Mapped[int] = mapped_column(
        Integer,
        default=200,
        server_default="200",
        nullable=False,
    )
    status: Mapped[MonitorStatus] = mapped_column(
        Enum(
            MonitorStatus,
            name="monitor_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        default=MonitorStatus.UNKNOWN,
        server_default=MonitorStatus.UNKNOWN.value,
        nullable=False,
    )
    failure_threshold: Mapped[int] = mapped_column(
        Integer,
        default=3,
        server_default="3",
        nullable=False,
    )
    recovery_threshold: Mapped[int] = mapped_column(
        Integer,
        default=2,
        server_default="2",
        nullable=False,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    consecutive_successes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_check_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
