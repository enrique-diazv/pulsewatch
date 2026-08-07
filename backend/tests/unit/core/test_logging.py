import json
import logging

from app.core.logging import (
    REDACTED_VALUE,
    JsonFormatter,
    configure_logging,
)


def test_json_formatter_creates_structured_log() -> None:
    record = logging.LogRecord(
        name="pulsewatch.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="monitor_check_completed",
        args=(),
        exc_info=None,
    )
    record.monitor_id = "monitor-123"
    record.response_time_ms = 184

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "pulsewatch.tests"
    assert payload["event"] == "monitor_check_completed"
    assert payload["monitor_id"] == "monitor-123"
    assert payload["response_time_ms"] == 184
    assert "timestamp" in payload


def test_json_formatter_redacts_sensitive_values() -> None:
    record = logging.LogRecord(
        name="pulsewatch.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=30,
        msg="authentication_attempt",
        args=(),
        exc_info=None,
    )
    record.details = {
        "password": "do-not-log",
        "authorization": "Bearer secret-token",
        "nested": [
            {
                "api-key": "secret-api-key",
                "status": "visible",
            }
        ],
    }
    record.refresh_token = "secret-refresh-token"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["details"]["password"] == REDACTED_VALUE
    assert payload["details"]["authorization"] == REDACTED_VALUE
    assert payload["details"]["nested"][0]["api-key"] == REDACTED_VALUE
    assert payload["details"]["nested"][0]["status"] == "visible"
    assert payload["refresh_token"] == REDACTED_VALUE


def test_configure_logging_sets_level_and_handler() -> None:
    logger = configure_logging("WARNING")

    json_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler.formatter, JsonFormatter)
    ]

    try:
        assert logger.level == logging.WARNING
        assert logger.propagate is False
        assert len(json_handlers) == 1
    finally:
        for handler in json_handlers:
            logger.removeHandler(handler)
            handler.close()
