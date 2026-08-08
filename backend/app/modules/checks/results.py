from dataclasses import dataclass, field
from enum import StrEnum


class CheckErrorType(StrEnum):
    UNSAFE_TARGET = "UNSAFE_TARGET"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TOO_MANY_REDIRECTS = "TOO_MANY_REDIRECTS"
    RESPONSE_TOO_LARGE = "RESPONSE_TOO_LARGE"
    UNEXPECTED_STATUS = "UNEXPECTED_STATUS"


@dataclass(frozen=True, slots=True)
class HttpCheckResult:
    success: bool
    status_code: int | None
    response_time_ms: int
    error_type: CheckErrorType | None = None
    error_message: str | None = None
    body: bytes = field(
        default=b"",
        repr=False,
    )
