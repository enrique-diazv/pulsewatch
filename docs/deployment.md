# PulseWatch production deployment

This document describes how to deploy PulseWatch using the production
Docker Compose stack.

## Architecture

The production stack contains:

- Nginx serving the React frontend and proxying `/api`.
- FastAPI running with multiple Uvicorn workers.
- Celery workers processing monitoring and notification jobs.
- Celery Beat scheduling periodic tasks.
- PostgreSQL storing application data.
- Redis acting as the Celery broker, cache, and Pub/Sub transport.
- Alembic applying database migrations before the API starts.

Only the frontend port is exposed publicly. PostgreSQL, Redis, and the
backend remain inside the Compose network.

## Required configuration

Copy the repository-level environment example:

```shell
cp .env.example .env