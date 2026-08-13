#!/bin/sh

set -eu

echo "Applying database migrations..."
python -m alembic upgrade head

echo "Starting Celery worker..."
python -m celery \
    -A app.workers.celery_app:celery_app \
    worker \
    --loglevel=INFO \
    --queues=monitoring,notifications \
    --pool=solo \
    --concurrency="${WORKER_CONCURRENCY:-1}" &

echo "Starting Celery Beat..."
python -m celery \
    -A app.workers.celery_app:celery_app \
    beat \
    --loglevel=INFO \
    --schedule=/tmp/celerybeat-schedule &

echo "Starting PulseWatch API..."
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-10000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --proxy-headers