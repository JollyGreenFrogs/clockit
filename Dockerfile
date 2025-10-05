# ClockIt - Cloud-Ready Time Tracker
# Multi-stage Docker build for production deployment

# Frontend build stage
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY react-frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source code
COPY react-frontend/ ./

# Build frontend for production
RUN npm run build

# Backend builder stage
FROM python:3.12-slim as backend-builder

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
    CLOCKIT_DATA_DIR=/app/data \
    CLOCKIT_DEV_MODE=false

# Install system dependencies for production
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r clockit && useradd -r -g clockit clockit

# Create application directories
RUN mkdir -p /app/data /app/logs /app/frontend && \
    chmod 755 /app && \
    chown -R clockit:clockit /app

# Copy Python packages from builder
COPY --from=backend-builder /root/.local /home/clockit/.local

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /app/frontend/dist /app/frontend/

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
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set working directory
WORKDIR /app

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]