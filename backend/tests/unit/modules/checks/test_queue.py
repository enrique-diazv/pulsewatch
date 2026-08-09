from unittest.mock import patch
from uuid import uuid4

from app.modules.checks.queue import enqueue_monitor_check


def test_enqueue_monitor_check_sends_only_monitor_id() -> None:
    monitor_id = uuid4()

    with patch("app.modules.checks.queue.check_monitor.delay") as delay:
        delay.return_value.id = "task-id"

        task_id = enqueue_monitor_check(monitor_id)

    assert task_id == "task-id"
    delay.assert_called_once_with(str(monitor_id))
