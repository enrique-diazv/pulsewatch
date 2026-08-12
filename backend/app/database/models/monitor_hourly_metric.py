from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MonitorHourlyMetric(Base):
    __tablename__ = "monitor_hourly_metrics"
    __table_args__ = (
        CheckConstraint(
            "total_checks > 0",
            name="hourly_metrics_total_checks_positive",
        ),
        CheckConstraint(
            """
            total_checks =
                successful_checks + failed_checks
            """,
            name="hourly_metrics_check_counts_consistent",
        ),
        CheckConstraint(
            """
            successful_checks >= 0
            AND failed_checks >= 0
            """,
            name="hourly_metrics_check_counts_nonnegative",
        ),
        CheckConstraint(
            """
            average_response_time_ms >= 0
            AND min_response_time_ms >= 0
            AND max_response_time_ms >= 0
            AND min_response_time_ms <= max_response_time_ms
            """,
            name="hourly_metrics_response_times_valid",
        ),
        CheckConstraint(
            "uptime_percentage BETWEEN 0 AND 100",
            name="hourly_metrics_uptime_percentage_range",
        ),
        Index(
            "ix_monitor_hourly_metrics_hour",
            "hour",
        ),
    )

    monitor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitors.id", ondelete="CASCADE"),
        primary_key=True,
    )
    hour: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
    )
    total_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    successful_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    failed_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    average_response_time_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    min_response_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    max_response_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    uptime_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
