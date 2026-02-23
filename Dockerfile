# HuggingFace Models Explorer - Dockerfile for Cloud Run
# Multi-stage build for optimized image size

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml .

# Install dependencies into a virtual environment
# UV_PROJECT_ENVIRONMENT tells uv where to install packages
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv venv /opt/venv && \
    uv sync --no-dev --no-editable

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (respecting .dockerignore)
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup data/ ./data/
COPY --chown=appuser:appgroup static/ ./static/

# Set environment variables
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check - useful for Cloud Run and local testing
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=5)" || exit 1

# Run the application directly (no uv run in production for faster startup)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
