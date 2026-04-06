# Stage 1: Build frontend (skippable for GovCloud headless deployment)
ARG INCLUDE_FRONTEND=true
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + optional frontend
FROM python:3.11-slim AS runtime
WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY backend/app/ ./app/
COPY backend/tenants/ ./tenants/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini ./

# Built frontend (conditional — omit for headless GovCloud deployment)
ARG INCLUDE_FRONTEND=true
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Non-root user for security (CMMC 3.1.1)
RUN useradd --create-home --shell /bin/bash corvus
USER corvus

# Default env
ENV PORT=8002
ENV TENANT_ID=corvus-aero
ENV AZURE_OPENAI_API_KEY=""
ENV AZURE_OPENAI_ENDPOINT=""
ENV AZURE_OPENAI_API_VERSION="2024-10-21"
ENV AZURE_OPENAI_DEPLOYMENT_GPT4O=""
ENV AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI=""
ENV AZURE_OPENAI_DEPLOYMENT_O1=""
ENV LLM_MODEL_ALIASES=""
ENV RBAC_MODE="disabled"

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:${PORT}/admin/health-check || exit 1

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
