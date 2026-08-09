from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.database.models.user import User
from app.database.session import get_database_session
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.exceptions import IncidentNotFoundError


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


def create_incident() -> Incident:
    started_at = datetime(2026, 8, 9, 12, 30, tzinfo=UTC)

    return Incident(
        id=uuid4(),
        monitor_id=uuid4(),
        started_at=started_at,
        resolved_at=None,
        status=IncidentStatus.OPEN,
        failure_reason="Request timed out",
        initial_check_id=42,
        recovery_check_id=None,
    )


def test_list_incidents_returns_owned_incidents(
    client: TestClient,
    current_user: User,
) -> None:
    incident = create_incident()

    with patch(
        "app.api.v1.endpoints.incidents.IncidentService.list_for_user",
        new_callable=AsyncMock,
        return_value=[incident],
    ) as list_for_user:
        response = client.get(
            "/api/v1/incidents?status=OPEN",
        )

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(incident.id)
    assert response.json()[0]["status"] == "OPEN"
    assert response.json()[0]["failure_reason"] == "Request timed out"
    list_for_user.assert_awaited_once_with(
        current_user.id,
        status=IncidentStatus.OPEN,
    )


def test_get_incident_returns_owned_incident(
    client: TestClient,
) -> None:
    incident = create_incident()

    with patch(
        "app.api.v1.endpoints.incidents.IncidentService.get_for_user",
        new_callable=AsyncMock,
        return_value=incident,
    ):
        response = client.get(
            f"/api/v1/incidents/{incident.id}",
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(incident.id)


def test_get_incident_hides_unowned_incident(
    client: TestClient,
) -> None:
    incident_id = uuid4()

    with patch(
        "app.api.v1.endpoints.incidents.IncidentService.get_for_user",
        new_callable=AsyncMock,
        side_effect=IncidentNotFoundError,
    ):
        response = client.get(
            f"/api/v1/incidents/{incident_id}",
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Incident not found",
    }


def test_incidents_require_authentication(
    database_session: AsyncMock,
) -> None:
    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/incidents")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_list_incidents_rejects_invalid_status(
    client: TestClient,
) -> None:
    with patch(
        "app.api.v1.endpoints.incidents.IncidentService.list_for_user",
        new_callable=AsyncMock,
    ) as list_for_user:
        response = client.get(
            "/api/v1/incidents?status=INVALID",
        )

    assert response.status_code == 422
    list_for_user.assert_not_awaited()
