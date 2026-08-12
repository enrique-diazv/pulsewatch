FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system pulsewatch \
    && useradd \
        --system \
        --gid pulsewatch \
        --create-home \
        pulsewatch

COPY requirements.txt ./

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        --requirement requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

RUN chown --recursive pulsewatch:pulsewatch /app

USER pulsewatch

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3)"]

CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --proxy-headers"]