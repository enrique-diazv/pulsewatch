from time import perf_counter

from app.integrations.redis import create_redis_client
from app.workers.celery_app import celery_app

TASK_NAME = "app.workers.monitor_tasks.check_monitor"
QUEUE_NAME = "pulsewatch-load-test"
MONITOR_ID = "00000000-0000-0000-0000-000000000001"
BATCH_SIZES = (
    100,
    1_000,
    5_000,
    10_000,
)


def enqueue_batch(
    count: int,
    producer: object,
) -> tuple[float, float]:
    started_at = perf_counter()

    for _ in range(count):
        celery_app.send_task(
            TASK_NAME,
            args=(MONITOR_ID,),
            queue=QUEUE_NAME,
            producer=producer,
            ignore_result=True,
        )

    elapsed_seconds = perf_counter() - started_at
    tasks_per_second = count / elapsed_seconds

    return elapsed_seconds, tasks_per_second


def main() -> None:
    redis_client = create_redis_client()

    try:
        redis_client.ping()

        with celery_app.producer_or_acquire() as producer:
            celery_app.send_task(
                TASK_NAME,
                args=(MONITOR_ID,),
                queue=QUEUE_NAME,
                producer=producer,
                ignore_result=True,
            )
            redis_client.delete(QUEUE_NAME)

            print(
                "tasks | queued | seconds | tasks_per_second",
            )

            for count in BATCH_SIZES:
                redis_client.delete(QUEUE_NAME)

                elapsed_seconds, tasks_per_second = enqueue_batch(
                    count,
                    producer,
                )
                queued_tasks = redis_client.llen(
                    QUEUE_NAME,
                )

                if queued_tasks != count:
                    raise RuntimeError(
                        "Unexpected queue length: "
                        f"expected {count}, got {queued_tasks}",
                    )

                print(
                    f"{count:>5} | "
                    f"{queued_tasks:>6} | "
                    f"{elapsed_seconds:>7.3f} | "
                    f"{tasks_per_second:>16.2f}",
                )
    finally:
        redis_client.delete(QUEUE_NAME)
        redis_client.close()


if __name__ == "__main__":
    main()
