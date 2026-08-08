import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.modules.checks.results import HttpCheckResult


class AssertionType(StrEnum):
    STATUS_CODE = "STATUS_CODE"
    BODY_CONTAINS = "BODY_CONTAINS"
    JSON_PATH = "JSON_PATH"
    RESPONSE_TIME = "RESPONSE_TIME"


@dataclass(frozen=True, slots=True)
class CheckAssertion:
    type: AssertionType
    expected_value: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class AssertionEvaluation:
    success: bool
    message: str | None = None


def evaluate_assertion(
    assertion: CheckAssertion,
    result: HttpCheckResult,
) -> AssertionEvaluation:
    match assertion.type:
        case AssertionType.STATUS_CODE:
            success = _matches_status(assertion, result)
        case AssertionType.BODY_CONTAINS:
            success = assertion.expected_value.encode("utf-8") in result.body
        case AssertionType.JSON_PATH:
            success = _matches_json_path(assertion, result)
        case AssertionType.RESPONSE_TIME:
            success = _matches_response_time(assertion, result)

    if success:
        return AssertionEvaluation(success=True)

    return AssertionEvaluation(
        success=False,
        message=f"Assertion failed: {assertion.type.value}",
    )


def _matches_status(
    assertion: CheckAssertion,
    result: HttpCheckResult,
) -> bool:
    try:
        expected_status = int(assertion.expected_value)
    except ValueError:
        return False

    return result.status_code == expected_status


def _matches_response_time(
    assertion: CheckAssertion,
    result: HttpCheckResult,
) -> bool:
    try:
        maximum_milliseconds = int(assertion.expected_value)
    except ValueError:
        return False

    return result.response_time_ms < maximum_milliseconds


def _matches_json_path(
    assertion: CheckAssertion,
    result: HttpCheckResult,
) -> bool:
    if assertion.field is None:
        return False

    try:
        current_value: Any = json.loads(result.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False

    for path_part in assertion.field.split("."):
        if not isinstance(current_value, dict):
            return False

        if path_part not in current_value:
            return False

        current_value = current_value[path_part]

    return current_value == _parse_expected_value(
        assertion.expected_value,
    )


def _parse_expected_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
