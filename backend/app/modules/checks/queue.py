from uuid import UUID

from app.workers.monitor_tasks import check_monitor


def enqueue_monitor_check(monitor_id: UUID) -> str:
    task = check_monitor.delay(str(monitor_id))

    return str(task.id)
