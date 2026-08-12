from time import perf_counter, sleep, time_ns
from uuid import uuid4

from redis import Redis

from app.integrations.redis import create_redis_client
from app.workers.celery_app import celery_app

TASK_NAME = "pulsewatch.load_tests.consume_probe"
QUEUE_NAME = "pulsewatch-load-test-consumer"
RESULT_TTL_SECONDS = 3_600
COMPLETION_TIMEOUT_SECONDS = 600
BATCH_SIZES = (
    100,
    1_000,
    5_000,
    10_000,
)

_worker_redis: Redis | None = None


def result_key(
    run_id: str,
    metric: str,
) -> str:
    return f"load-test:{run_id}:{metric}"


def worker_redis() -> Redis:
    global _worker_redis

    if _worker_redis is None:
        _worker_redis = create_redis_client()

    return _worker_redis


@celery_app.task(name=TASK_NAME)
def consume_probe(
    run_id: str,
    enqueued_at_ns: int,
) -> None:
    started_at_ns = time_ns()
    finished_at_ns = time_ns()

    queue_latency_ms = (started_at_ns - enqueued_at_ns) / 1_000_000
    processing_time_ms = (finished_at_ns - started_at_ns) / 1_000_000

    latency_key = result_key(
        run_id,
        "queue-latency-ms",
    )
    processing_key = result_key(
        run_id,
        "processing-time-ms",
    )
    processed_key = result_key(
        run_id,
        "processed",
    )

    pipeline = worker_redis().pipeline(
        transaction=False,
    )
    pipeline.rpush(
        latency_key,
        queue_latency_ms,
    )
    pipeline.rpush(
        processing_key,
        processing_time_ms,
    )
    pipeline.incr(processed_key)
    pipeline.expire(
        latency_key,
        RESULT_TTL_SECONDS,
    )
    pipeline.expire(
        processing_key,
        RESULT_TTL_SECONDS,
    )
    pipeline.expire(
        processed_key,
        RESULT_TTL_SECONDS,
    )
    pipeline.execute()


def percentile(
    values: list[float],
    percentage: float,
) -> float:
    ordered_values = sorted(values)
    position = (len(ordered_values) - 1) * percentage
    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(ordered_values) - 1,
    )
    fraction = position - lower_index

    return (
        ordered_values[lower_index]
        + (ordered_values[upper_index] - ordered_values[lower_index]) * fraction
    )


def wait_for_completion(
    redis_client: Redis,
    run_id: str,
    expected_count: int,
) -> None:
    processed_key = result_key(
        run_id,
        "processed",
    )
    deadline = perf_counter() + COMPLETION_TIMEOUT_SECONDS

    while perf_counter() < deadline:
        processed = int(
            redis_client.get(processed_key) or 0,
        )

        if processed >= expected_count:
            return

        sleep(0.05)

    raise TimeoutError(
        f"Only {processed} of {expected_count} tasks completed",
    )


def read_metric(
    redis_client: Redis,
    run_id: str,
    metric: str,
) -> list[float]:
    return [
        float(value)
        for value in redis_client.lrange(
            result_key(run_id, metric),
            0,
            -1,
        )
    ]


def delete_run_results(
    redis_client: Redis,
    run_id: str,
) -> None:
    redis_client.delete(
        result_key(
            run_id,
            "queue-latency-ms",
        ),
        result_key(
            run_id,
            "processing-time-ms",
        ),
        result_key(
            run_id,
            "processed",
        ),
    )


def run_batch(
    redis_client: Redis,
    producer: object,
    count: int,
) -> None:
    run_id = uuid4().hex
    started_at = perf_counter()

    try:
        for _ in range(count):
            celery_app.send_task(
                TASK_NAME,
                args=(
                    run_id,
                    time_ns(),
                ),
                queue=QUEUE_NAME,
                producer=producer,
                ignore_result=True,
            )

        depth_after_publish = redis_client.llen(
            QUEUE_NAME,
        )

        wait_for_completion(
            redis_client,
            run_id,
            count,
        )

        total_seconds = perf_counter() - started_at
        jobs_per_second = count / total_seconds
        queue_latencies = read_metric(
            redis_client,
            run_id,
            "queue-latency-ms",
        )
        processing_times = read_metric(
            redis_client,
            run_id,
            "processing-time-ms",
        )

        print(
            f"{count:>5} | "
            f"{depth_after_publish:>5} | "
            f"{total_seconds:>7.3f} | "
            f"{jobs_per_second:>9.2f} | "
            f"{percentile(queue_latencies, 0.50):>8.2f} | "
            f"{percentile(queue_latencies, 0.95):>8.2f} | "
            f"{percentile(queue_latencies, 0.99):>8.2f} | "
            f"{percentile(processing_times, 0.95):>8.4f}",
        )
    finally:
        delete_run_results(
            redis_client,
            run_id,
        )


def main() -> None:
    redis_client = create_redis_client()

    try:
        redis_client.ping()
        redis_client.delete(QUEUE_NAME)

        print(
            "tasks | depth | seconds | "
            "jobs/sec | queue p50 | queue p95 | "
            "queue p99 | task p95",
        )

        with celery_app.producer_or_acquire() as producer:
            for count in BATCH_SIZES:
                run_batch(
                    redis_client,
                    producer,
                    count,
                )
    finally:
        redis_client.delete(QUEUE_NAME)
        redis_client.close()


if __name__ == "__main__":
    main()
