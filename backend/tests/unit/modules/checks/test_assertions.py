from app.modules.checks.assertions import (
    AssertionType,
    CheckAssertion,
    evaluate_assertion,
)
from app.modules.checks.results import HttpCheckResult


def create_result(
    *,
    status_code: int = 200,
    response_time_ms: int = 184,
    body: bytes = b"",
) -> HttpCheckResult:
    return HttpCheckResult(
        success=True,
        status_code=status_code,
        response_time_ms=response_time_ms,
        body=body,
    )


def test_status_code_assertion() -> None:
    assertion = CheckAssertion(
        type=AssertionType.STATUS_CODE,
        expected_value="200",
    )

    assert evaluate_assertion(
        assertion,
        create_result(status_code=200),
    ).success
    assert not evaluate_assertion(
        assertion,
        create_result(status_code=503),
    ).success


def test_body_contains_assertion() -> None:
    assertion = CheckAssertion(
        type=AssertionType.BODY_CONTAINS,
        expected_value="healthy",
    )

    evaluation = evaluate_assertion(
        assertion,
        create_result(body=b"service is healthy"),
    )

    assert evaluation.success


def test_json_path_assertion() -> None:
    assertion = CheckAssertion(
        type=AssertionType.JSON_PATH,
        field="data.status",
        expected_value="active",
    )

    evaluation = evaluate_assertion(
        assertion,
        create_result(
            body=b'{"data":{"status":"active"}}',
        ),
    )

    assert evaluation.success


def test_json_path_assertion_rejects_missing_path() -> None:
    assertion = CheckAssertion(
        type=AssertionType.JSON_PATH,
        field="data.status",
        expected_value="active",
    )

    evaluation = evaluate_assertion(
        assertion,
        create_result(body=b'{"data":{}}'),
    )

    assert not evaluation.success


def test_response_time_assertion_uses_strict_limit() -> None:
    assertion = CheckAssertion(
        type=AssertionType.RESPONSE_TIME,
        expected_value="1000",
    )

    assert evaluate_assertion(
        assertion,
        create_result(response_time_ms=999),
    ).success
    assert not evaluate_assertion(
        assertion,
        create_result(response_time_ms=1000),
    ).success


def test_json_path_assertion_rejects_invalid_json() -> None:
    assertion = CheckAssertion(
        type=AssertionType.JSON_PATH,
        field="status",
        expected_value="active",
    )

    evaluation = evaluate_assertion(
        assertion,
        create_result(body=b"not-json"),
    )

    assert not evaluation.success
