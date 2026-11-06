# ---- Backend Dockerfile (multi‑stage) ----
# Builder stage
FROM python:3.11-slim AS builder
# Install build‑time dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Install requirements in an isolated layer
COPY backend/requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Application stage
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    # Use non‑root user
    APP_USER=appuser \
    APP_GROUP=appgroup
RUN addgroup --system $APP_GROUP && adduser --system --ingroup $APP_GROUP $APP_USER

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/app ./app
COPY backend/scripts ./scripts
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini

# Ensure proper permissions
RUN chown -R $APP_USER:$APP_GROUP /app
USER $APP_USER

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

