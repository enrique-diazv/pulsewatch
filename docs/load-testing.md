# PulseWatch load-testing report

Status: local engineering baseline  
Test date: August 12, 2026

## Purpose

These tests evaluate PulseWatch API latency, error rate, Redis/Celery
job publication, and synthetic worker consumption.

The results are measurements from a local development environment.
They are not production-capacity claims.

## Test environment

| Component | Value |
| --- | --- |
| CPU | AMD Ryzen 5 4600H |
| Physical cores | 6 |
| Logical processors | 12 |
| Memory | 23.36 GB |
| Operating system | Windows 11 Home 10.0.26200 |
| Python | 3.13.14 |
| Node.js | 24.18.0 |
| PostgreSQL | 18.4 |
| Memurai | 4.2.3 |
| Redis compatibility | 7.4.9 |
| k6 | 2.2.0 |

The API, PostgreSQL, Memurai, Celery, and k6 load generator ran on the
same computer. FastAPI ran in development mode with its reload process.
Celery used the Windows-compatible `solo` pool.

These conditions introduce resource contention and differ from a
production deployment with dedicated hosts and multiple API or worker
processes.

## Test scripts

- [`smoke.js`](../load-tests/api/smoke.js)
- [`read-load.js`](../load-tests/api/read-load.js)
- [`mixed-load.js`](../load-tests/api/mixed-load.js)
- [`enqueue_benchmark.py`](../load-tests/workers/enqueue_benchmark.py)
- [`consumer_benchmark.py`](../load-tests/workers/consumer_benchmark.py)

## API targets

| Endpoint | Target |
| --- | ---: |
| Cached dashboard summary | p95 < 300 ms |
| Monitor list | p95 < 300 ms |
| Monitor metrics | p95 < 300 ms |
| Check history | p95 < 400 ms |
| Expected-response error rate | < 1% |

## Smoke test

The smoke test used up to 5 virtual users for 50 seconds.

| Metric | Result |
| --- | ---: |
| Requests | 207 |
| Throughput | 4.10 requests/s |
| Error rate | 0% |
| Global p95 | 9.75 ms |
| Dashboard p95 | 15.47 ms |
| Monitor list p95 | 8.39 ms |
| Check history p95 | 9.49 ms |
| Monitor metrics p95 | 9.08 ms |

All smoke-test thresholds passed.

## Sustained read test

The read test gradually increased traffic to 50 virtual users over
three minutes.

| Metric | Result |
| --- | ---: |
| Requests | 5,982 |
| Throughput | 33.16 requests/s |
| Error rate | 0% |
| Maximum VUs | 50 |
| Global p95 | 9.47 ms |
| Dashboard p95 | 9.50 ms |
| Monitor list p95 | 7.73 ms |
| Check history p95 | 9.82 ms |
| Monitor metrics p95 | 9.86 ms |

All sustained-read thresholds passed.

## Mixed workload

The representative mixed workload used the following distribution:

- 70% reads
- 15% monitor updates
- 5% manual checks
- 10% login requests

Manual-check responses with status `202 Accepted` and `429 Too Many
Requests` were both expected. The latter confirms enforcement of the
manual-check cooldown under repeated load.

The test used up to 25 virtual users for three minutes.

### Initial result

| Metric | Result |
| --- | ---: |
| Requests | 2,645 |
| Throughput | 14.65 requests/s |
| Error rate | 0% |
| Global p95 | 315.96 ms |
| Dashboard p95 | 316.48 ms |
| Monitor list p95 | 279.16 ms |
| Check history p95 | 355.91 ms |
| Monitor metrics p95 | 318.52 ms |

The dashboard and metrics p95 targets failed by 16.48 ms and 18.52 ms,
respectively.

The read-only test had remained fast at 50 VUs, so the degradation was
not caused primarily by the read queries.

### Root cause

Argon2 hashing and password verification were running synchronously
inside asynchronous authentication service methods.

Concurrent login requests blocked the FastAPI event loop and increased
latency for unrelated read endpoints.

Password hashing and verification were moved to worker threads with
`asyncio.to_thread`.

### Result after optimization

| Metric | Result |
| --- | ---: |
| Requests | 2,761 |
| Throughput | 15.29 requests/s |
| Error rate | 0% |
| Successful checks | 2,761 of 2,761 |
| Global median | 8.18 ms |
| Global p95 | 86.39 ms |
| Global maximum | 254.05 ms |
| Dashboard p95 | 14.20 ms |
| Monitor list p95 | 11.40 ms |
| Check history p95 | 14.87 ms |
| Monitor metrics p95 | 14.41 ms |

All mixed-load thresholds passed after the change.

Global p95 decreased by approximately 72.7%. The read endpoint p95
values decreased by more than 95% compared with the initial mixed run.

This result demonstrates why CPU-intensive password hashing must not run
directly on an asynchronous event loop.

## Celery job-publication benchmark

The producer published jobs to an isolated Redis queue without a worker
consuming them. Queue depth was verified after every batch.

| Jobs | Queue depth | Publish time | Publish throughput |
| ---: | ---: | ---: | ---: |
| 100 | 100 | 0.127 s | 789.32 jobs/s |
| 1,000 | 1,000 | 0.757 s | 1,321.67 jobs/s |
| 5,000 | 5,000 | 2.515 s | 1,988.02 jobs/s |
| 10,000 | 10,000 | 4.997 s | 2,001.30 jobs/s |

The isolated queue was deleted after the benchmark and its final depth
was zero.

This benchmark measures serialization and Redis/Celery publication. It
does not measure HTTP-check execution.

## Synthetic worker-consumption benchmark

A dedicated Celery worker consumed synthetic probe tasks from an
isolated queue. It used the `solo` pool and did not contact external
websites or APIs.

The depth column is the queue depth immediately after the producer
finished publishing.

| Jobs | Depth | Total time | Throughput | Queue p50 | Queue p95 | Queue p99 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 59 | 0.251 s | 398.66 jobs/s | 49.48 ms | 121.00 ms | 126.67 ms |
| 1,000 | 594 | 1.655 s | 604.17 jobs/s | 506.72 ms | 884.21 ms | 908.85 ms |
| 5,000 | 3,033 | 7.160 s | 698.32 jobs/s | 2,337.94 ms | 3,766.05 ms | 3,913.26 ms |
| 10,000 | 6,004 | 13.373 s | 747.77 jobs/s | 4,063.56 ms | 7,278.73 ms | 7,552.98 ms |

All tasks completed and the final queue depth was zero.

The producer reached approximately 2,001 jobs/s, while one synthetic
worker consumed approximately 748 jobs/s. This implies that roughly
three equivalent synthetic workers would be needed to absorb that
publication rate without sustained queue growth.

That estimate is an architectural planning value, not an HTTP-monitor
capacity claim. Real check throughput depends on endpoint latency,
timeouts, connection pooling, database work, incident processing, and
notification activity.

## Security of test artifacts

A raw k6 summary export can include setup data such as access tokens.

Raw JSON summaries are therefore excluded through:

```gitignore
/load-tests/results/*.json