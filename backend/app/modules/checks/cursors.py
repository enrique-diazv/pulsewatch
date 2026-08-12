from base64 import b64decode, urlsafe_b64encode
from binascii import Error as Base64Error
from dataclasses import dataclass
from datetime import UTC, datetime


class InvalidCheckCursorError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CheckCursor:
    checked_at: datetime
    check_id: int


def encode_check_cursor(
    checked_at: datetime,
    check_id: int,
) -> str:
    if checked_at.utcoffset() is None:
        raise ValueError("Cursor timestamp must include a timezone")

    if check_id <= 0:
        raise ValueError("Cursor check id must be positive")

    normalized_timestamp = checked_at.astimezone(UTC)
    payload = (f"{normalized_timestamp.isoformat()}|{check_id}").encode()

    return urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_check_cursor(cursor: str) -> CheckCursor:
    try:
        padding = "=" * (-len(cursor) % 4)
        payload = b64decode(
            cursor + padding,
            altchars=b"-_",
            validate=True,
        ).decode("utf-8")
        timestamp_value, check_id_value = payload.rsplit(
            "|",
            maxsplit=1,
        )
        checked_at = datetime.fromisoformat(timestamp_value)
        check_id = int(check_id_value)
    except (
        Base64Error,
        UnicodeDecodeError,
        ValueError,
    ) as error:
        raise InvalidCheckCursorError("Invalid monitor check cursor") from error

    if checked_at.utcoffset() is None or check_id <= 0:
        raise InvalidCheckCursorError("Invalid monitor check cursor")

    return CheckCursor(
        checked_at=checked_at.astimezone(UTC),
        check_id=check_id,
    )
