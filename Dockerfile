# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + built frontend
FROM python:3.11-slim AS runtime
WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY backend/app/ ./app/
COPY backend/tenants/ ./tenants/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini ./

# Built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Default env
ENV PORT=8002
ENV TENANT_ID=corvus-aero

EXPOSE ${PORT}

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
