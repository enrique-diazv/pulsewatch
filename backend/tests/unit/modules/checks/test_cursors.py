from datetime import (
    UTC,
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.modules.checks.cursors import (
    InvalidCheckCursorError,
    decode_check_cursor,
    encode_check_cursor,
)


def test_check_cursor_round_trip_normalizes_to_utc() -> None:
    checked_at = datetime(
        2026,
        8,
        12,
        9,
        30,
        tzinfo=UTC,
    )

    cursor = encode_check_cursor(
        checked_at,
        321,
    )
    decoded = decode_check_cursor(cursor)

    assert decoded.checked_at == checked_at
    assert decoded.check_id == 321
    assert "|" not in cursor


def test_check_cursor_preserves_an_instant_across_timezones() -> None:
    checked_at = datetime(
        2026,
        8,
        12,
        3,
        30,
        tzinfo=timezone_offset(),
    )

    decoded = decode_check_cursor(encode_check_cursor(checked_at, 42))

    assert decoded.checked_at == datetime(
        2026,
        8,
        12,
        9,
        30,
        tzinfo=UTC,
    )


def timezone_offset():
    return timezone(timedelta(hours=-6))


@pytest.mark.parametrize(
    "cursor",
    [
        "not-base64!",
        "bm90LWFuLWludmFsaWQtY3Vyc29y",
        "",
    ],
)
def test_decode_rejects_invalid_cursor(
    cursor: str,
) -> None:
    with pytest.raises(
        InvalidCheckCursorError,
        match="Invalid monitor check cursor",
    ):
        decode_check_cursor(cursor)


def test_encode_rejects_naive_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timestamp must include a timezone",
    ):
        encode_check_cursor(
            datetime(2026, 8, 12),
            1,
        )
