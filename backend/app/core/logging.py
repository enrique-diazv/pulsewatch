import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime

LOGGER_NAME = "pulsewatch"
REDACTED_VALUE = "[REDACTED]"

SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "cookie",
    "password",
    "passwd",
    "secret",
    "token",
)

STANDARD_LOG_RECORD_ATTRIBUTES = frozenset(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
)


def _is_sensitive_key(key: str) -> bool:
    normalized_key = key.casefold().replace("-", "_")
    return any(
        sensitive_part in normalized_key for sensitive_part in SENSITIVE_KEY_PARTS
    )


def _redact(value: object, key: str | None = None) -> object:
    if key is not None and _is_sensitive_key(key):
        return REDACTED_VALUE

    if isinstance(value, Mapping):
        return {
            str(nested_key): _redact(
                nested_value,
                str(nested_key),
            )
            for nested_key, nested_value in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]

    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in STANDARD_LOG_RECORD_ATTRIBUTES and not key.startswith("_"):
                payload[key] = _redact(value, key)

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            default=str,
            ensure_ascii=False,
        )


def configure_logging(log_level: str) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)

    for handler in logger.handlers[:]:
        if isinstance(handler.formatter, JsonFormatter):
            logger.removeHandler(handler)
            handler.close()

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)
    logger.setLevel(log_level)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{name}")
