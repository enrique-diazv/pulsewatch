from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor_check import MonitorCheck
from app.modules.checks.cursors import (
    CheckCursor,
    decode_check_cursor,
)
from app.modules.checks.repository import MonitorCheckRepository


@pytest.mark.anyio
async def test_add_flushes_monitor_check() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = MonitorCheckRepository(session)
    monitor_check = MonitorCheck(
        monitor_id=uuid4(),
        success=True,
        status_code=200,
        response_time_ms=125,
        error_type=None,
        error_message=None,
    )

    added_monitor_check = await repository.add(monitor_check)

    assert added_monitor_check is monitor_check
    session.add.assert_called_once_with(monitor_check)
    session.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_list_for_monitor_returns_latest_checks_first() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitor_id = uuid4()
    checks = [
        MonitorCheck(
            monitor_id=monitor_id,
            success=True,
            status_code=200,
            response_time_ms=125,
        ),
        MonitorCheck(
            monitor_id=monitor_id,
            success=False,
            status_code=503,
            response_time_ms=450,
        ),
    ]
    result.scalars.return_value.all.return_value = checks
    session.execute.return_value = result
    repository = MonitorCheckRepository(session)

    found_checks = await repository.list_for_monitor(
        monitor_id,
        limit=50,
    )

    assert found_checks == checks

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert f"monitor_checks.monitor_id = '{monitor_id}'" in sql
    assert ("ORDER BY monitor_checks.checked_at DESC, monitor_checks.id DESC") in sql
    assert "LIMIT 50" in sql


@pytest.mark.anyio
async def test_list_page_uses_cursor_and_detects_next_page() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitor_id = uuid4()
    first_timestamp = datetime(
        2026,
        8,
        12,
        10,
        tzinfo=UTC,
    )
    checks = [
        MonitorCheck(
            id=3,
            monitor_id=monitor_id,
            checked_at=first_timestamp,
            success=True,
            status_code=200,
            response_time_ms=100,
        ),
        MonitorCheck(
            id=2,
            monitor_id=monitor_id,
            checked_at=first_timestamp,
            success=True,
            status_code=200,
            response_time_ms=110,
        ),
        MonitorCheck(
            id=1,
            monitor_id=monitor_id,
            checked_at=first_timestamp,
            success=False,
            status_code=503,
            response_time_ms=450,
        ),
    ]
    result.scalars.return_value.all.return_value = checks
    session.execute.return_value = result
    repository = MonitorCheckRepository(session)
    cursor = CheckCursor(
        checked_at=datetime(
            2026,
            8,
            12,
            11,
            tzinfo=UTC,
        ),
        check_id=4,
    )

    page = await repository.list_page_for_monitor(
        monitor_id,
        limit=2,
        cursor=cursor,
    )

    assert page.items == checks[:2]
    assert page.next_cursor is not None

    decoded_cursor = decode_check_cursor(page.next_cursor)

    assert decoded_cursor.checked_at == first_timestamp
    assert decoded_cursor.check_id == 2

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "monitor_checks.checked_at <" in sql
    assert "monitor_checks.checked_at =" in sql
    assert "monitor_checks.id < 4" in sql
    assert "LIMIT 3" in sql


@pytest.mark.anyio
async def test_list_page_omits_cursor_on_last_page() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitor_id = uuid4()
    checks = [
        MonitorCheck(
            id=2,
            monitor_id=monitor_id,
            checked_at=datetime(
                2026,
                8,
                12,
                10,
                tzinfo=UTC,
            ),
            success=True,
            status_code=200,
            response_time_ms=100,
        ),
        MonitorCheck(
            id=1,
            monitor_id=monitor_id,
            checked_at=datetime(
                2026,
                8,
                12,
                9,
                tzinfo=UTC,
            ),
            success=True,
            status_code=200,
            response_time_ms=120,
        ),
    ]
    result.scalars.return_value.all.return_value = checks
    session.execute.return_value = result
    repository = MonitorCheckRepository(session)

    page = await repository.list_page_for_monitor(
        monitor_id,
        limit=2,
    )

    assert page.items == checks
    assert page.next_cursor is None


@pytest.mark.anyio
async def test_summarize_for_monitor_aggregates_selected_range() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.one.return_value = SimpleNamespace(
        total_checks=10,
        successful_checks=8,
        average_response_time_ms=Decimal("147.5"),
    )
    session.execute.return_value = result
    repository = MonitorCheckRepository(session)
    monitor_id = uuid4()
    from_timestamp = datetime(2026, 8, 8, tzinfo=UTC)
    to_timestamp = datetime(2026, 8, 9, tzinfo=UTC)

    summary = await repository.summarize_for_monitor(
        monitor_id,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
    )

    assert summary.total_checks == 10
    assert summary.successful_checks == 8
    assert summary.average_response_time_ms == 147.5

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert f"monitor_checks.monitor_id = '{monitor_id}'" in sql
    assert "monitor_checks.checked_at >=" in sql
    assert "monitor_checks.checked_at <" in sql
    assert "monitor_checks.checked_at <=" not in sql
    assert "count(monitor_checks.id)" in sql
    assert "avg(monitor_checks.response_time_ms)" in sql
