from datetime import UTC, datetime
from uuid import uuid4

from app.database.models.incident import Incident
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.schemas import IncidentResponse


def test_incident_response_reads_model_attributes() -> None:
    started_at = datetime(2026, 8, 9, 10, 30, tzinfo=UTC)
    incident = Incident(
        id=uuid4(),
        monitor_id=uuid4(),
        started_at=started_at,
        resolved_at=None,
        status=IncidentStatus.OPEN,
        failure_reason="Request timed out",
        initial_check_id=42,
        recovery_check_id=None,
    )

    response = IncidentResponse.model_validate(incident)

    assert response.id == incident.id
    assert response.monitor_id == incident.monitor_id
    assert response.started_at == started_at
    assert response.resolved_at is None
    assert response.status is IncidentStatus.OPEN
    assert response.failure_reason == "Request timed out"
    assert response.initial_check_id == 42
    assert response.recovery_check_id is None
