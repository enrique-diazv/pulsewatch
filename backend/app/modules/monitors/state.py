from dataclasses import dataclass

from app.modules.monitors.enums import MonitorStatus


@dataclass(frozen=True, slots=True)
class MonitorStateUpdate:
    status: MonitorStatus
    consecutive_failures: int
    consecutive_successes: int
    went_down: bool = False
    recovered: bool = False


def evaluate_monitor_state(
    *,
    current_status: MonitorStatus,
    check_succeeded: bool,
    consecutive_failures: int,
    consecutive_successes: int,
    failure_threshold: int,
    recovery_threshold: int,
) -> MonitorStateUpdate:
    if current_status is MonitorStatus.PAUSED:
        return MonitorStateUpdate(
            status=current_status,
            consecutive_failures=consecutive_failures,
            consecutive_successes=consecutive_successes,
        )

    if check_succeeded:
        updated_successes = consecutive_successes + 1

        if (
            current_status is MonitorStatus.DOWN
            and updated_successes < recovery_threshold
        ):
            updated_status = MonitorStatus.DOWN
        else:
            updated_status = MonitorStatus.UP

        return MonitorStateUpdate(
            status=updated_status,
            consecutive_failures=0,
            consecutive_successes=updated_successes,
            recovered=(
                current_status is MonitorStatus.DOWN
                and updated_status is MonitorStatus.UP
            ),
        )

    updated_failures = consecutive_failures + 1
    updated_status = current_status

    if updated_failures >= failure_threshold:
        updated_status = MonitorStatus.DOWN

    return MonitorStateUpdate(
        status=updated_status,
        consecutive_failures=updated_failures,
        consecutive_successes=0,
        went_down=(
            current_status is not MonitorStatus.DOWN
            and updated_status is MonitorStatus.DOWN
        ),
    )
