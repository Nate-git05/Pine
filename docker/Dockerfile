FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# Install only the server's pinned Python dependencies. Runtime credentials are
# provided by Cloud Run and must not be copied into the image.
COPY server/requirements.txt ./server/requirements.txt
RUN python -m pip install --no-cache-dir -r server/requirements.txt

COPY --chown=10001:10001 server/ ./server/

# Run as a non-root user. Keep Uvicorn at one worker because the server's SSE
# event queues are process-local.
RUN adduser --disabled-password --gecos "" --uid 10001 pine
USER 10001:10001

EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
