# Stage 1: Builder stage - installs dependencies and packages the application
FROM python:3.13-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production stage - smaller and optimized
FROM python:3.13-slim as production

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/logs

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Create application directory and copy application code
RUN mkdir -p /app/api/v1/{routers,services,request_models,response_models} \
    /core/{caching,dependencies,scheduled_tasks,task_locking,utils}

# Copy application files
COPY main.py .
COPY config.py .
COPY api/ ./api/
COPY core/ ./core/

# Copy environment file if it exists
COPY .env .env

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]