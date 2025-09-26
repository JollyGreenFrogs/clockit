# ClockIt - Cloud-Ready Time Tracker
# Multi-stage Docker build for production deployment

FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CLOCKIT_DATA_DIR=/app/data

# Create non-root user
RUN groupadd -r clockit && useradd -r -g clockit clockit

# Create application directories
RUN mkdir -p /app/data /app/logs && \
    chmod 755 /app && \
    chown -R clockit:clockit /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/clockit/.local

# Copy application code
COPY src/ /app/src/
COPY pyproject.toml /app/

# Set proper ownership
RUN chown -R clockit:clockit /app

# Switch to non-root user
USER clockit

# Update PATH to include local packages
ENV PATH=/home/clockit/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Set working directory
WORKDIR /app

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]