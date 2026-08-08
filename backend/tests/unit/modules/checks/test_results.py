from app.modules.checks.results import (
    CheckErrorType,
    HttpCheckResult,
)


def test_http_check_result_represents_success() -> None:
    result = HttpCheckResult(
        success=True,
        status_code=200,
        response_time_ms=184,
        body=b'{"status":"healthy"}',
    )

    assert result.success is True
    assert result.status_code == 200
    assert result.error_type is None
    assert result.body == b'{"status":"healthy"}'


def test_http_check_result_hides_body_from_representation() -> None:
    result = HttpCheckResult(
        success=False,
        status_code=500,
        response_time_ms=220,
        error_type=CheckErrorType.UNEXPECTED_STATUS,
        error_message="Expected HTTP 200 but received 500",
        body=b"sensitive response content",
    )

    assert "sensitive response content" not in repr(result)
