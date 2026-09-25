# Dockerfile for Gericure Health Memory System (Phase 3)
# Multi-stage build for optimized production image

# ============================================================================
# STAGE 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create wheels for all dependencies
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# ============================================================================
# STAGE 2: Runtime
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="Gericure Dev Team <dev@gericure.com>"
LABEL description="AI-Powered Persistent Health Memory for Elderly Patients"
LABEL version="3.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app \
    LOG_LEVEL=INFO

WORKDIR ${APP_HOME}

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

# Install Python dependencies from wheels
RUN pip install --no-cache /wheels/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy application code
COPY --chown=appuser:appuser . ${APP_HOME}

# Create necessary directories
RUN mkdir -p ${APP_HOME}/logs \
    && mkdir -p ${APP_HOME}/data \
    && chown -R appuser:appuser ${APP_HOME}

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
# Shell form so $PORT (injected by Railway/most PaaS platforms) actually
# gets expanded at container start. Falls back to 8000 for plain `docker run`.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
