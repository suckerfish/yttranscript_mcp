# Multi-stage build for YouTube Transcript MCP Server
# Optimized for 2025 Docker best practices

# Build stage - Install dependencies and build wheels
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files
WORKDIR /app
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e .

# Production stage - Minimal runtime environment
FROM python:3.11-alpine AS production

# Install runtime dependencies including ffmpeg for yt-dlp
RUN apk add --no-cache \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN adduser -D -s /bin/sh appuser

# Set working directory
WORKDIR /app

# Copy application source code
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV YT_TRANSCRIPT_SERVER_HOST=0.0.0.0
ENV YT_TRANSCRIPT_SERVER_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command - run with uvicorn for HTTP transport
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]