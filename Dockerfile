# ==============================================================================
# Multi-Stage Production Dockerfile for NEXORA Enterprise Business OS
# Builds React + TypeScript frontend cleanly and serves via FastAPI + Uvicorn
# ==============================================================================

FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runner
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN useradd -m -u 10001 nexora && chown -R nexora:nexora /app
USER nexora

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
ENV APP_ENV=production
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://127.0.0.1:${PORT}/api/health || exit 1

CMD ["sh", "-c", "python backend/scripts/bootstrap_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
