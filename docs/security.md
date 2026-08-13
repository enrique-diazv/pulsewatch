# PulseWatch security

PulseWatch accepts URLs from users and performs network requests on their
behalf. Its security model therefore protects both user accounts and the
infrastructure running the monitoring workers.

## Authentication and sessions

- Passwords are hashed with Argon2. Plaintext passwords are never persisted.
- Successful login issues a short-lived JWT access token.
- Refresh tokens are cryptographically random and only their SHA-256 hashes are
  stored in PostgreSQL.
- Refresh tokens are rotated on use. Logout revokes the stored token.
- The raw refresh token is sent in an HTTP-only cookie restricted to the auth
  path. Production cookies use `Secure` and `SameSite=Lax`.
- Invalid, expired, revoked, or missing credentials return an authentication
  error without exposing token details.

Access tokens are kept separate from the refresh-token cookie. A stolen
database alone does not reveal reusable refresh tokens, while rotation limits
the lifetime of a captured token.

## Authorization and data ownership

Authentication alone is not treated as authorization. Repository queries for
monitors, checks, incidents, metrics, dashboard summaries, and notifications
are scoped to the authenticated user.

Resource identifiers supplied by a client are validated against ownership on
the server. The frontend is not trusted to enforce tenant isolation.

## SSRF protection

Server-side request forgery is the primary application-specific threat because
monitor targets are user controlled. Before every outbound request, PulseWatch:

1. Allows only HTTP and HTTPS URLs.
2. Rejects embedded URL credentials.
3. Resolves the hostname before connecting.
4. Rejects non-global, private, loopback, link-local, multicast, reserved, and
   unspecified IPv4 or IPv6 addresses.
5. Revalidates every redirect destination.
6. Limits redirect count, request duration, and response-body size.
7. Converts unsafe targets and network failures into classified check results.

These controls prevent monitors from being used to reach services such as
localhost, private databases, Redis, cloud metadata endpoints, or other
internal network resources.

## Background-work safety

- Scheduled HTTP checks execute in Celery workers, outside API request
  processes.
- A Redis lock prevents concurrent execution of the same monitor. Locks expire
  so an interrupted worker cannot block it permanently.
- Database row locking protects monitor state transitions and incident
  thresholds from concurrent updates.
- Database claiming and rescheduling prevent the scheduler from enqueueing the
  same due monitor repeatedly.
- Manual checks use a per-user and per-monitor Redis cooldown.
- Notification workers use bounded retry counts and per-notification locks.

## WebSocket security

The browser cannot open a private event stream using only a user identifier.
It first requests a short-lived, random ticket through an authenticated REST
endpoint. Redis stores only the ticket hash and consumes it atomically, making
the ticket single-use.

After validation, FastAPI subscribes the socket to the authenticated user's
private Redis channel. Published events contain the minimum state required for
frontend query invalidation.

## Input, storage, and transport controls

- Pydantic validates API payloads and SQLAlchemy uses parameterized queries.
- PostgreSQL constraints enforce status ranges, nonnegative counters,
  notification consistency, and one open incident per monitor.
- CORS accepts only configured origins.
- Production traffic is expected to use HTTPS; Nginx or the hosting platform
  terminates TLS.
- Secrets and connection strings come from environment variables and are not
  committed to Git.
- Structured JSON logging redacts keys containing password, authorization,
  cookie, secret, token, or API-key material.
- API, PostgreSQL, and Redis remain internal in the canonical Compose topology;
  only the frontend reverse proxy exposes a host port.

## Deployment checklist

Before a production deployment:

- Replace every placeholder secret and use a high-entropy `JWT_SECRET_KEY`.
- Set the exact public HTTPS origin in `APP_ORIGIN` and the CORS allowlist.
- Use TLS-enabled PostgreSQL and Redis connections where required.
- Keep production `.env` files outside version control.
- Restrict database and Redis network access to application services.
- Apply Alembic migrations before starting API and worker processes.
- Review logs and monitoring without recording credentials or private payloads.
- Rotate credentials immediately if a secret is exposed.

## Residual risks and scope

The current project does not claim protection against every production threat.
Important future hardening includes account verification and recovery flows,
global login throttling, multi-factor authentication, dependency and container
scanning, a managed secret store, centralized audit logs, and an external
security review.

The free portfolio deployment also combines API, worker, and scheduler in one
small service. This is a cost-driven demo compromise, not the recommended
isolation model for a high-risk or high-volume environment.
