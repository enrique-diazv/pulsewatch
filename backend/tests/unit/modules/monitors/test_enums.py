from app.modules.monitors.enums import HttpMethod, MonitorStatus


def test_monitor_status_has_expected_values() -> None:
    assert {status.value for status in MonitorStatus} == {
        "UP",
        "DOWN",
        "DEGRADED",
        "PAUSED",
        "UNKNOWN",
    }


def test_initial_http_method_only_supports_get() -> None:
    assert list(HttpMethod) == [HttpMethod.GET]
    assert HttpMethod.GET.value == "GET"
