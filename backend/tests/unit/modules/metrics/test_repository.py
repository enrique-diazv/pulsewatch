from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.metrics.repository import (
    HourlyMetricRepository,
)


@pytest.mark.anyio
async def test_upsert_hour_executes_aggregation_statement() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.rowcount = 3
    session.execute.return_value = result
    repository = HourlyMetricRepository(session)
    hour = datetime(2026, 8, 12, 10, tzinfo=UTC)

    affected_rows = await repository.upsert_hour(hour)

    assert affected_rows == 3
    session.execute.assert_awaited_once()

    statement = session.execute.await_args.args[0]
    compiled = str(statement.compile())

    assert "monitor_hourly_metrics" in compiled
    assert "ON CONFLICT" in compiled
    assert "monitor_checks.checked_at" in compiled


@pytest.mark.anyio
async def test_summarize_for_monitor_returns_weighted_metrics() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.one.return_value = SimpleNamespace(
        total_checks=120,
        successful_checks=118,
        average_response_time_ms=175.25,
    )
    session.execute.return_value = result
    repository = HourlyMetricRepository(session)
    monitor_id = uuid4()
    from_hour = datetime(
        2026,
        8,
        5,
        tzinfo=UTC,
    )
    to_hour = datetime(
        2026,
        8,
        12,
        tzinfo=UTC,
    )

    summary = await repository.summarize_for_monitor(
        monitor_id,
        from_hour=from_hour,
        to_hour=to_hour,
    )

    assert summary.total_checks == 120
    assert summary.successful_checks == 118
    assert summary.average_response_time_ms == 175.25
    session.execute.assert_awaited_once()
