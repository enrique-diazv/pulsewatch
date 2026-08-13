# PulseWatch architecture

This document describes the implemented PulseWatch architecture and the
reasoning behind its main boundaries.

## System context

PulseWatch accepts user-defined public HTTP endpoints, checks them on a
schedule, stores results, detects state changes, creates or resolves incidents,
and updates the authenticated frontend.

~~~mermaid
flowchart LR
    User["User browser"]
    Target["Public website or API"]
    Email["Email provider or structured log"]

    subgraph PulseWatch
        Frontend["React frontend"]
        API["FastAPI"]
        Database[("PostgreSQL")]
        Redis[("Redis")]
        Worker["Celery workers"]
        Beat["Celery Beat"]
    end

    User <-->|"HTTPS / WebSocket"| Frontend
    Frontend <-->|"REST / WebSocket"| API
    API <-->|"Queries / transactions"| Database
    API <-->|"Cache / rate limits / Pub/Sub"| Redis
    Beat -->|"Periodic jobs"| Redis
    Redis -->|"Monitoring and notification queues"| Worker
    Worker <-->|"Results / incidents / metrics"| Database
    Worker <-->|"Locks / cache invalidation / Pub/Sub"| Redis
    Worker -->|"Validated HTTP requests"| Target
    Worker -->|"Incident and recovery messages"| Email
~~~

The API never performs scheduled monitoring requests. External HTTP work runs
in Celery workers so API latency and worker capacity can scale independently.

## Backend layers

The backend follows a router-service-repository structure:

~~~text
FastAPI router
    -> application service
        -> repository
            -> SQLAlchemy async session
                -> PostgreSQL
~~~

- Routers translate HTTP input and output, enforce authentication, and map
  domain errors to status codes.
- Services own authentication, monitor, check, incident, notification, metrics,
  dashboard, and scheduling behavior.
- Repositories isolate database queries and ownership-aware data access.
- Workers invoke the same services used by HTTP workflows instead of
  duplicating business logic.

## Scheduled check lifecycle

~~~mermaid
sequenceDiagram
    autonumber
    participant Beat as Celery Beat
    participant Scheduler as Scheduler task
    participant DB as PostgreSQL
    participant Queue as Redis / Celery
    participant Worker as Monitor worker
    participant Lock as Redis lock
    participant Target as Target endpoint
    participant Realtime as Redis Pub/Sub
    participant API as FastAPI WebSocket
    participant UI as React UI

    Beat->>Scheduler: schedule_due_monitors
    Scheduler->>DB: claim active monitors where next_check_at <= now
    DB-->>Scheduler: monitor IDs and rescheduled next_check_at
    loop Each claimed monitor
        Scheduler->>Queue: enqueue check_monitor(monitor_id)
    end
    Queue->>Worker: deliver monitoring job
    Worker->>Lock: acquire monitor lock
    alt Lock acquired
        Worker->>DB: load active monitor
        Worker->>Target: validated HTTP request
        Target-->>Worker: response or classified failure
        Worker->>DB: lock row and store MonitorCheck
        Worker->>DB: update counters and monitor state
        Worker->>DB: open or resolve incident when threshold is met
        Worker->>DB: commit transaction
        Worker->>Realtime: publish monitor and incident events
        Realtime->>API: private user channel
        API->>UI: authenticated WebSocket event
    else Lock busy
        Worker-->>Queue: skip duplicate execution
    end
~~~

### Check safety controls

Before contacting a target, the HTTP engine:

1. Accepts only supported HTTP schemes.
2. Resolves the hostname.
3. Rejects private, loopback, link-local, multicast, reserved, and unsafe
   addresses.
4. Revalidates redirect destinations.
5. Limits redirects, response size, and execution time.
6. Classifies HTTP, connection, timeout, TLS, response-size, and unsafe-target
   failures.

The distributed lock has a TTL so an interrupted worker cannot block a monitor
forever.

## Incidents and notifications

A single failed check does not immediately create an incident. The monitor
state service maintains consecutive failure and success counters.

~~~mermaid
stateDiagram-v2
    [*] --> UNKNOWN
    UNKNOWN --> UP: successful check
    UNKNOWN --> DOWN: failure threshold reached
    UP --> DOWN: failure threshold reached
    DOWN --> UP: recovery threshold reached
    UP --> PAUSED: user pauses monitor
    DOWN --> PAUSED: user pauses monitor
    UNKNOWN --> PAUSED: user pauses monitor
    PAUSED --> UNKNOWN: user resumes monitor
~~~

When an incident opens or resolves, the same database transaction creates a
pending notification. A periodic dispatcher publishes notification jobs to a
dedicated queue. Workers use per-notification Redis locks, enforce retry
limits, and deliver through either structured logs or SMTP.

## Real-time updates

The browser obtains a short-lived, single-use WebSocket ticket through an
authenticated REST request. FastAPI atomically consumes the ticket from Redis
and subscribes the connection to a private user channel.

Workers publish only event identifiers and state required to invalidate or
refresh affected frontend queries. A Redis or WebSocket outage does not roll
back an already committed check; the UI can recover through normal REST
refetching.

## Metrics, history, and retention

- Recent check history uses stable cursor pagination ordered by
  `(checked_at DESC, id DESC)`.
- The 24-hour range reads raw checks.
- Longer ranges combine hourly aggregates with raw boundary data.
- Celery Beat runs hourly aggregation jobs.
- Retention jobs remove expired raw checks in bounded batches while preserving
  checks referenced by incidents.
- Dashboard summaries use short-lived, per-user Redis cache entries that are
  invalidated after relevant worker activity.

These choices keep common reads bounded as monitor history grows.

## Data ownership and security boundaries

- Every user-owned query enforces ownership on the server.
- Passwords use Argon2 and are never stored in plaintext.
- Access tokens are short-lived JWTs.
- Refresh tokens are random, stored only as hashes, rotated, revoked, and sent
  through secure HTTP-only cookies.
- WebSocket tickets are random, hashed, expiring, and single-use.
- Redis provides cooldown rate limits for manual checks and distributed locks.
- Structured logs exclude passwords, tokens, authorization headers, and
  monitor secrets.
- Configuration and secrets come from environment variables.

## Technical decisions

| Decision | Reasoning and trade-off |
| --- | --- |
| Modular monolith | Domain modules share one deployable codebase, keeping the MVP understandable while preserving service and repository boundaries for later extraction. |
| PostgreSQL as the system of record | Transactions, constraints, row locks, partial indexes, and Alembic migrations provide stronger consistency than an eventually consistent store. |
| Redis for ephemeral coordination | Celery queues, distributed locks, cooldowns, short-lived cache entries, WebSocket tickets, and Pub/Sub need low latency but are not the authoritative business record. |
| Monitoring outside API processes | Celery keeps unpredictable external HTTP latency away from user-facing request handling. It adds operational components but allows worker capacity to scale separately. |
| Database claiming plus Redis locks | Database claiming prevents duplicate scheduling, while expiring per-monitor locks prevent overlapping execution. The two mechanisms protect different concurrency boundaries. |
| Raw checks plus hourly aggregates | Raw rows preserve recent detail; hourly buckets keep longer-range metrics bounded. This adds aggregation and retention jobs in exchange for predictable reads. |
| Short access tokens plus rotating refresh tokens | Access tokens keep API authorization stateless. Hashed, revocable refresh tokens provide longer sessions without storing reusable raw tokens. |
| Events trigger query invalidation | WebSocket messages remain small and REST stays authoritative. A missed event causes a later refetch rather than permanent client divergence. |
| Separate canonical and demo topologies | Compose demonstrates production isolation. The free public demo combines processes only to satisfy zero-cost hosting constraints. |

## Canonical production deployment

The production Compose stack keeps infrastructure responsibilities separate:

~~~mermaid
flowchart TB
    Internet[Internet]

    subgraph Host[Production host]
        Nginx[Nginx and React]
        API[FastAPI and Uvicorn workers]
        Migrate[One-shot Alembic migration]
        Worker[Celery workers]
        Beat[Celery Beat]
        Postgres[(PostgreSQL)]
        Redis[(Redis)]
    end

    Internet -->|Only exposed port| Nginx
    Nginx -->|API and WebSocket proxy| API
    API --> Postgres
    API --> Redis
    Migrate --> Postgres
    Beat --> Redis
    Redis --> Worker
    Worker --> Postgres
    Worker --> Redis
~~~

PostgreSQL, Redis, the API, and worker processes remain internal. Migrations
must succeed before the API, workers, and scheduler start.

## Zero-cost portfolio deployment

The public demo preserves application behavior while fitting free-tier
constraints:

~~~mermaid
flowchart LR
    Browser[Browser]
    Vercel[Vercel Hobby - React and API rewrite]
    Render[Render Free - FastAPI, Worker, and Beat]
    Neon[(Neon Free - PostgreSQL)]
    RenderRedis[(Render Free - Key Value)]
    Target[Public target]

    Browser <-->|HTTPS| Vercel
    Browser <-->|Direct WebSocket| Render
    Vercel -->|API rewrite| Render
    Render --> Neon
    Render --> RenderRedis
    Render --> Target
~~~

This is intentionally a demo topology:

- Render can suspend the web service after inactivity, so monitoring pauses
  while the container is asleep and the first request can have a cold start.
- API, worker, and Beat share one small instance instead of scaling
  independently.
- Free Key Value persistence is disabled.
- Email delivery uses log mode because free Render services restrict common
  outbound SMTP ports.

The canonical Compose topology remains the production reference.

## Scaling path

No domain redesign is required to scale beyond the demo:

1. Run multiple Uvicorn processes or API instances behind a load balancer.
2. Move workers and Beat into separate services.
3. Add workers to the monitoring queue horizontally.
4. Keep exactly one logical scheduler, with database claiming preventing
   duplicate scheduling.
5. Use managed PostgreSQL and Redis with connection limits sized for API and
   worker concurrency.
6. Partition or archive raw check history when retention volume requires it.
7. Add queue-depth, queue-latency, check-duration, incident, database, and
   process telemetry.

Measured local API and worker baselines are documented in
[load-testing.md](load-testing.md). Deployment configuration is documented in
[deployment.md](deployment.md).
