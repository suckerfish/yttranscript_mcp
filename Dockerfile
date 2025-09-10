FROM python:3.11-slim

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Install uv (pinned version for reproducibility)
RUN pip install --no-cache-dir uv==0.8.15

# Copy dependency files first (for better caching)
COPY pyproject.toml ./
COPY README.md ./
COPY uv.lock* ./

# Copy application code (needed for package installation)
COPY src/ ./src/

# Install dependencies in a separate layer (cached unless dependencies change)
RUN uv pip install --system --no-cache .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV YT_TRANSCRIPT_SERVER_HOST=0.0.0.0
ENV YT_TRANSCRIPT_SERVER_PORT=8080

# Expose port
EXPOSE 8080

# Health check with lightweight curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the server with HTTP transport
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]