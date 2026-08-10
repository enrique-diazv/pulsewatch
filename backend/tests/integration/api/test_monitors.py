from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.database.models.monitor_check import MonitorCheck
from app.database.models.user import User
from app.database.session import get_database_session
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.checks.schemas import MonitorMetricsResponse
from app.modules.monitors.enums import HttpMethod, MonitorStatus
from app.modules.monitors.exceptions import MonitorNotFoundError


@pytest.fixture
def current_user() -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        password_hash="hashed-password",
    )


@pytest.fixture
def database_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def client(
    current_user: User,
    database_session: AsyncMock,
) -> Iterator[TestClient]:
    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def create_monitor(user_id: UUID) -> Monitor:
    timestamp = datetime(2026, 8, 8, tzinfo=UTC)

    return Monitor(
        id=uuid4(),
        user_id=user_id,
        name="Production API",
        url="https://api.example.com/health",
        method=HttpMethod.GET,
        interval_seconds=60,
        timeout_seconds=5,
        expected_status=200,
        status=MonitorStatus.UNKNOWN,
        failure_threshold=3,
        recovery_threshold=2,
        consecutive_failures=0,
        consecutive_successes=0,
        is_active=True,
        last_checked_at=None,
        next_check_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )


def create_monitor_check(
    monitor_id: UUID,
    *,
    check_id: int = 1,
) -> MonitorCheck:
    timestamp = datetime(2026, 8, 9, tzinfo=UTC)

    return MonitorCheck(
        id=check_id,
        monitor_id=monitor_id,
        checked_at=timestamp,
        success=True,
        status_code=200,
        response_time_ms=125,
        error_type=None,
        error_message=None,
    )


def test_create_monitor_returns_owned_monitor(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.create",
        new_callable=AsyncMock,
        return_value=monitor,
    ) as create:
        response = client.post(
            "/api/v1/monitors",
            json={
                "name": "Production API",
                "url": "https://api.example.com/health",
            },
        )

    assert response.status_code == 201
    assert response.json()["id"] == str(monitor.id)
    assert response.json()["name"] == "Production API"
    assert response.json()["status"] == "UNKNOWN"
    assert "user_id" not in response.json()
    create.assert_awaited_once()


def test_list_monitors_returns_owned_monitors(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.list_for_user",
        new_callable=AsyncMock,
        return_value=[monitor],
    ):
        response = client.get("/api/v1/monitors")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(monitor.id)
    assert "user_id" not in response.json()[0]


def test_get_monitor_returns_owned_monitor(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
        new_callable=AsyncMock,
        return_value=monitor,
    ):
        response = client.get(f"/api/v1/monitors/{monitor.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(monitor.id)


def test_get_monitor_returns_not_found_for_unowned_monitor(
    client: TestClient,
) -> None:
    monitor_id = uuid4()

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
        new_callable=AsyncMock,
        side_effect=MonitorNotFoundError,
    ):
        response = client.get(f"/api/v1/monitors/{monitor_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}


def test_monitors_require_authentication(
    database_session: AsyncMock,
) -> None:
    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/monitors")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_update_monitor_returns_updated_monitor(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)
    monitor.name = "Updated API"
    monitor.interval_seconds = 120

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.update",
        new_callable=AsyncMock,
        return_value=monitor,
    ) as update:
        response = client.patch(
            f"/api/v1/monitors/{monitor.id}",
            json={
                "name": "Updated API",
                "interval_seconds": 120,
            },
        )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated API"
    assert response.json()["interval_seconds"] == 120
    update.assert_awaited_once()


def test_update_monitor_rejects_empty_body(
    client: TestClient,
) -> None:
    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.update",
        new_callable=AsyncMock,
    ) as update:
        response = client.patch(
            f"/api/v1/monitors/{uuid4()}",
            json={},
        )

    assert response.status_code == 422
    update.assert_not_awaited()


def test_delete_monitor_returns_no_content(
    client: TestClient,
) -> None:
    monitor_id = uuid4()

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.delete",
        new_callable=AsyncMock,
    ) as delete:
        response = client.delete(
            f"/api/v1/monitors/{monitor_id}",
        )

    assert response.status_code == 204
    assert response.content == b""
    delete.assert_awaited_once()


def test_pause_monitor_returns_paused_monitor(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)
    monitor.is_active = False
    monitor.status = MonitorStatus.PAUSED

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.pause",
        new_callable=AsyncMock,
        return_value=monitor,
    ):
        response = client.post(
            f"/api/v1/monitors/{monitor.id}/pause",
        )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["status"] == "PAUSED"


def test_resume_monitor_returns_unknown_active_monitor(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)

    with patch(
        "app.api.v1.endpoints.monitors.MonitorService.resume",
        new_callable=AsyncMock,
        return_value=monitor,
    ):
        response = client.post(
            f"/api/v1/monitors/{monitor.id}/resume",
        )

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert response.json()["status"] == "UNKNOWN"


def test_manual_check_queues_owned_monitor(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            return_value=monitor,
        ) as get_for_user,
        patch(
            "app.api.v1.endpoints.monitors.enqueue_monitor_check",
            return_value="task-id",
        ) as enqueue,
        patch(
            "app.api.v1.endpoints.monitors.reserve_manual_check_slot",
            new_callable=AsyncMock,
            return_value=True,
        ) as reserve,
    ):
        response = client.post(
            f"/api/v1/monitors/{monitor.id}/check",
        )

    assert response.status_code == 202
    assert response.json() == {
        "task_id": "task-id",
        "status": "queued",
    }
    get_for_user.assert_awaited_once_with(
        monitor.id,
        current_user.id,
    )
    reserve.assert_awaited_once_with(
        current_user.id,
        monitor.id,
    )
    enqueue.assert_called_once_with(monitor.id)


def test_manual_check_hides_unowned_monitor(
    client: TestClient,
) -> None:
    monitor_id = uuid4()

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            side_effect=MonitorNotFoundError,
        ),
        patch(
            "app.api.v1.endpoints.monitors.enqueue_monitor_check",
        ) as enqueue,
    ):
        response = client.post(
            f"/api/v1/monitors/{monitor_id}/check",
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}
    enqueue.assert_not_called()


def test_manual_check_enforces_cooldown(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            return_value=monitor,
        ),
        patch(
            "app.api.v1.endpoints.monitors.reserve_manual_check_slot",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "app.api.v1.endpoints.monitors.enqueue_monitor_check",
        ) as enqueue,
    ):
        response = client.post(
            f"/api/v1/monitors/{monitor.id}/check",
        )

    assert response.status_code == 429
    assert response.json() == {
        "detail": "Manual check cooldown active",
    }
    assert response.headers["retry-after"] == "10"
    enqueue.assert_not_called()


def test_list_monitor_checks_returns_latest_checks(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)
    checks = [
        create_monitor_check(monitor.id, check_id=2),
        create_monitor_check(monitor.id, check_id=1),
    ]

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            return_value=monitor,
        ) as get_for_user,
        patch(
            "app.api.v1.endpoints.monitors.MonitorCheckRepository.list_for_monitor",
            new_callable=AsyncMock,
            return_value=checks,
        ) as list_for_monitor,
    ):
        response = client.get(
            f"/api/v1/monitors/{monitor.id}/checks?limit=50",
        )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [2, 1]
    assert response.json()[0]["monitor_id"] == str(monitor.id)
    assert response.json()[0]["response_time_ms"] == 125
    get_for_user.assert_awaited_once_with(
        monitor.id,
        current_user.id,
    )
    list_for_monitor.assert_awaited_once_with(
        monitor.id,
        limit=50,
    )


def test_list_monitor_checks_hides_unowned_monitor(
    client: TestClient,
) -> None:
    monitor_id = uuid4()

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            side_effect=MonitorNotFoundError,
        ),
        patch(
            "app.api.v1.endpoints.monitors.MonitorCheckRepository.list_for_monitor",
            new_callable=AsyncMock,
        ) as list_for_monitor,
    ):
        response = client.get(
            f"/api/v1/monitors/{monitor_id}/checks",
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}
    list_for_monitor.assert_not_awaited()


def test_list_monitor_checks_rejects_invalid_limit(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/monitors/{uuid4()}/checks?limit=501",
    )

    assert response.status_code == 422


def create_monitor_metrics(
    metrics_range: str = "24h",
) -> MonitorMetricsResponse:
    return MonitorMetricsResponse(
        range=metrics_range,
        from_timestamp=datetime(2026, 8, 8, tzinfo=UTC),
        to_timestamp=datetime(2026, 8, 9, tzinfo=UTC),
        total_checks=100,
        successful_checks=98,
        failed_checks=2,
        uptime_percentage=98.0,
        average_response_time_ms=145.25,
    )


def test_get_monitor_metrics_uses_default_range(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)
    metrics = create_monitor_metrics()

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            return_value=monitor,
        ) as get_for_user,
        patch(
            "app.api.v1.endpoints.monitors.MonitorMetricsService.summarize",
            new_callable=AsyncMock,
            return_value=metrics,
        ) as summarize,
    ):
        response = client.get(
            f"/api/v1/monitors/{monitor.id}/metrics",
        )

    assert response.status_code == 200
    assert response.json()["range"] == "24h"
    assert response.json()["total_checks"] == 100
    assert response.json()["uptime_percentage"] == 98.0
    assert response.json()["average_response_time_ms"] == 145.25
    get_for_user.assert_awaited_once_with(
        monitor.id,
        current_user.id,
    )
    summarize.assert_awaited_once_with(
        monitor.id,
        "24h",
    )


def test_get_monitor_metrics_accepts_explicit_range(
    client: TestClient,
    current_user: User,
) -> None:
    monitor = create_monitor(current_user.id)
    metrics = create_monitor_metrics("7d")

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            return_value=monitor,
        ),
        patch(
            "app.api.v1.endpoints.monitors.MonitorMetricsService.summarize",
            new_callable=AsyncMock,
            return_value=metrics,
        ) as summarize,
    ):
        response = client.get(
            f"/api/v1/monitors/{monitor.id}/metrics?range=7d",
        )

    assert response.status_code == 200
    assert response.json()["range"] == "7d"
    summarize.assert_awaited_once_with(
        monitor.id,
        "7d",
    )


def test_get_monitor_metrics_hides_unowned_monitor(
    client: TestClient,
) -> None:
    monitor_id = uuid4()

    with (
        patch(
            "app.api.v1.endpoints.monitors.MonitorService.get_for_user",
            new_callable=AsyncMock,
            side_effect=MonitorNotFoundError,
        ),
        patch(
            "app.api.v1.endpoints.monitors.MonitorMetricsService.summarize",
            new_callable=AsyncMock,
        ) as summarize,
    ):
        response = client.get(
            f"/api/v1/monitors/{monitor_id}/metrics",
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}
    summarize.assert_not_awaited()


def test_get_monitor_metrics_rejects_invalid_range(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/monitors/{uuid4()}/metrics?range=1h",
    )

    assert response.status_code == 422
