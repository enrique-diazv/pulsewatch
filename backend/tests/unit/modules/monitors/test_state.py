from app.modules.monitors.enums import MonitorStatus
from app.modules.monitors.state import evaluate_monitor_state


def test_first_success_marks_unknown_monitor_up() -> None:
    update = evaluate_monitor_state(
        current_status=MonitorStatus.UNKNOWN,
        check_succeeded=True,
        consecutive_failures=0,
        consecutive_successes=0,
        failure_threshold=3,
        recovery_threshold=2,
    )

    assert update.status is MonitorStatus.UP
    assert update.consecutive_failures == 0
    assert update.consecutive_successes == 1
    assert update.recovered is False


def test_failure_before_threshold_preserves_current_status() -> None:
    update = evaluate_monitor_state(
        current_status=MonitorStatus.UP,
        check_succeeded=False,
        consecutive_failures=0,
        consecutive_successes=4,
        failure_threshold=2,
        recovery_threshold=2,
    )

    assert update.status is MonitorStatus.UP
    assert update.consecutive_failures == 1
    assert update.consecutive_successes == 0
    assert update.went_down is False


def test_failure_threshold_marks_monitor_down() -> None:
    update = evaluate_monitor_state(
        current_status=MonitorStatus.UP,
        check_succeeded=False,
        consecutive_failures=1,
        consecutive_successes=0,
        failure_threshold=2,
        recovery_threshold=2,
    )

    assert update.status is MonitorStatus.DOWN
    assert update.consecutive_failures == 2
    assert update.went_down is True


def test_down_monitor_waits_for_recovery_threshold() -> None:
    update = evaluate_monitor_state(
        current_status=MonitorStatus.DOWN,
        check_succeeded=True,
        consecutive_failures=3,
        consecutive_successes=0,
        failure_threshold=3,
        recovery_threshold=2,
    )

    assert update.status is MonitorStatus.DOWN
    assert update.consecutive_failures == 0
    assert update.consecutive_successes == 1
    assert update.recovered is False


def test_recovery_threshold_marks_monitor_up() -> None:
    update = evaluate_monitor_state(
        current_status=MonitorStatus.DOWN,
        check_succeeded=True,
        consecutive_failures=0,
        consecutive_successes=1,
        failure_threshold=3,
        recovery_threshold=2,
    )

    assert update.status is MonitorStatus.UP
    assert update.consecutive_successes == 2
    assert update.recovered is True


def test_paused_monitor_state_remains_unchanged() -> None:
    update = evaluate_monitor_state(
        current_status=MonitorStatus.PAUSED,
        check_succeeded=False,
        consecutive_failures=2,
        consecutive_successes=1,
        failure_threshold=3,
        recovery_threshold=2,
    )

    assert update.status is MonitorStatus.PAUSED
    assert update.consecutive_failures == 2
    assert update.consecutive_successes == 1
    assert update.went_down is False
    assert update.recovered is False
