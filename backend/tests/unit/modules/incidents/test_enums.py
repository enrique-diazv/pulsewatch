from app.modules.incidents.enums import IncidentStatus


def test_incident_status_values_are_stable() -> None:
    assert IncidentStatus.OPEN.value == "OPEN"
    assert IncidentStatus.RESOLVED.value == "RESOLVED"


def test_incident_status_is_string_compatible() -> None:
    assert IncidentStatus.OPEN == "OPEN"
    assert IncidentStatus.RESOLVED == "RESOLVED"
