# PulseWatch data model

PulseWatch uses PostgreSQL as its system of record. The schema separates user
identity, monitor configuration, raw execution history, incidents,
notifications, and hourly aggregates.

## Entity relationship diagram

~~~mermaid
erDiagram
    USER ||--o{ REFRESH_TOKEN : owns
    USER ||--o{ MONITOR : owns
    USER ||--o{ NOTIFICATION : receives
    MONITOR ||--o{ MONITOR_CHECK : records
    MONITOR ||--o{ INCIDENT : produces
    MONITOR ||--o{ MONITOR_HOURLY_METRIC : aggregates
    MONITOR_CHECK ||--o{ INCIDENT : opens
    MONITOR_CHECK o|--o{ INCIDENT : recovers
    INCIDENT ||--o{ NOTIFICATION : triggers

    USER {
        uuid id PK
        varchar email UK
        varchar password_hash
        boolean is_verified
        timestamptz created_at
        timestamptz updated_at
    }

    REFRESH_TOKEN {
        uuid id PK
        uuid user_id FK
        varchar token_hash UK
        timestamptz expires_at
        timestamptz revoked_at
        timestamptz created_at
    }

    MONITOR {
        uuid id PK
        uuid user_id FK
        varchar name
        varchar url
        enum method
        integer interval_seconds
        integer timeout_seconds
        integer expected_status
        enum status
        integer failure_threshold
        integer recovery_threshold
        integer consecutive_failures
        integer consecutive_successes
        boolean is_active
        timestamptz last_checked_at
        timestamptz next_check_at
        timestamptz created_at
        timestamptz updated_at
    }

    MONITOR_CHECK {
        bigint id PK
        uuid monitor_id FK
        timestamptz checked_at
        boolean success
        integer status_code
        integer response_time_ms
        varchar error_type
        varchar error_message
    }

    INCIDENT {
        uuid id PK
        uuid monitor_id FK
        timestamptz started_at
        timestamptz resolved_at
        enum status
        varchar failure_reason
        bigint initial_check_id FK
        bigint recovery_check_id FK
    }

    NOTIFICATION {
        uuid id PK
        uuid user_id FK
        uuid incident_id FK
        enum type
        enum status
        integer attempt_count
        varchar last_error
        timestamptz sent_at
        timestamptz created_at
    }

    MONITOR_HOURLY_METRIC {
        uuid monitor_id PK,FK
        timestamptz hour PK
        integer total_checks
        integer successful_checks
        integer failed_checks
        float average_response_time_ms
        integer min_response_time_ms
        integer max_response_time_ms
        float uptime_percentage
        timestamptz updated_at
    }
~~~

Nullable fields are shown without additional Mermaid notation. In particular,
`last_checked_at`, check failure details, `resolved_at`, `recovery_check_id`,
notification delivery details, and token revocation time may be null.

## Ownership boundaries

`users` is the ownership root:

- A user owns refresh tokens and monitors.
- Checks, incidents, and hourly metrics inherit ownership through a monitor.
- Notifications store both `user_id` and `incident_id` so private delivery
  queries remain direct while the incident relationship is preserved.
- Application repositories still enforce user ownership; foreign keys alone do
  not provide authorization.

## Lifecycle and deletion rules

- Deleting a user cascades to refresh tokens, monitors, and notifications.
- Deleting a monitor cascades to raw checks, incidents, and hourly metrics.
- Deleting an incident cascades to its notifications.
- An incident references the check that opened it and optionally the check that
  resolved it. Both references use `ON DELETE RESTRICT`, preventing retention
  cleanup from removing audit evidence that is still attached to an incident.
- Raw-check retention therefore deletes only expired checks that are not
  referenced by either incident check column.

## Integrity constraints

The database enforces important domain invariants in addition to Pydantic and
service validation:

- Monitor intervals are between 30 seconds and 24 hours; timeouts are between
  1 and 60 seconds.
- Expected and recorded HTTP status codes stay within 100 through 599.
- Failure and recovery thresholds stay between 1 and 10; consecutive counters
  cannot be negative.
- Response times cannot be negative.
- An open incident has no resolution timestamp or recovery check. A resolved
  incident requires both.
- Only one open incident may exist for a monitor.
- A notification type may be created only once per incident.
- A sent notification requires `sent_at`; pending and failed notifications
  must not have it.
- Hourly counts must be nonnegative and add up to `total_checks`; response-time
  bounds and uptime percentage must remain valid.

## Query-oriented indexes

The main indexes mirror production access patterns:

- `monitors(user_id, status)` supports user dashboards and filtering.
- `monitors(is_active, next_check_at)` supports due-monitor claiming.
- `monitor_checks(monitor_id, checked_at DESC, id DESC)` supports stable cursor
  pagination and recent history.
- `incidents(monitor_id, started_at)` supports monitor incident timelines.
- A partial unique index on `incidents(monitor_id)` where status is `OPEN`
  prevents duplicate active incidents under concurrency.
- Notification indexes support pending dispatch and per-user history.
- `monitor_hourly_metrics(hour)` supports aggregation retention and time-range
  queries; its composite primary key prevents duplicate monitor-hour buckets.

Schema evolution is managed through Alembic migrations in
[`backend/migrations/versions`](../backend/migrations/versions/).
