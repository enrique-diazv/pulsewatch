from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.modules.metrics.retention import (
    MonitorCheckRetentionRepository,
    MonitorCheckRetentionService,
)


def create_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key=("test-jwt-secret-key-with-at-least-32-characters"),
        raw_check_retention_days=30,
        retention_batch_size=100,
    )


@pytest.mark.anyio
async def test_delete_aggregated_before_builds_safe_query() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.rowcount = 25
    session.execute.return_value = result
    repository = MonitorCheckRetentionRepository(
        session,
    )

    deleted = await repository.delete_aggregated_before(
        datetime(2026, 7, 12, tzinfo=UTC),
        limit=100,
    )

    assert deleted == 25
    statement = session.execute.await_args.args[0]
    compiled = str(
        statement.compile(
            dialect=postgresql.dialect(),
        )
    )

    assert "retention_candidates" in compiled
    assert "date_trunc" in compiled
    assert "monitor_hourly_metrics" in compiled
    assert "incidents.initial_check_id" in compiled
    assert "incidents.recovery_check_id" in compiled


@pytest.mark.anyio
async def test_purge_deletes_in_bounded_batches() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(
        spec=MonitorCheckRetentionRepository,
    )
    repository.delete_aggregated_before.side_effect = [
        100,
        25,
    ]
    settings = create_settings()
    service = MonitorCheckRetentionService(
        session,
        settings,
        repository,
    )
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)

    deleted = await service.purge(now)

    assert deleted == 125
    cutoff = now - timedelta(days=30)
    assert repository.delete_aggregated_before.await_args_list == [
        ((cutoff,), {"limit": 100}),
        ((cutoff,), {"limit": 100}),
    ]
    assert session.commit.await_count == 2
