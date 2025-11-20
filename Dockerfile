# Multi-stage build: Node.js for Tailwind CSS, then Python for Django
FROM node:18-alpine AS tailwind-builder

WORKDIR /app

# Copy package files and install Node.js dependencies
COPY package*.json ./
RUN npm ci

# Copy Tailwind config and source files
COPY tailwind.config.js postcss.config.js ./
COPY static/ ./static/
COPY templates/ ./templates/

# Build Tailwind CSS
RUN npm run build

# Python stage for Django application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN addgroup --system --gid 1001 django && \
    adduser --system --uid 1001 --gid 1001 --no-create-home django

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY . .

# Copy built Tailwind CSS from previous stage
COPY --from=tailwind-builder /app/static/css/dist/ ./static/css/dist/

# Create directories and preserve initial media files
RUN mkdir -p /app/staticfiles /app/media /data && \
    cp -r /app/media /app/media_initial 2>/dev/null || mkdir -p /app/media_initial && \
    chmod +x /app/entrypoint.sh && \
    chown -R django:django /app /data

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Start Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120"]