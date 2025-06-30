# Multi-stage build: Get Node.js from official Node image
FROM node:20-slim AS node-base

# Main Python application image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Node.js binary and modules from node-base stage
COPY --from=node-base /usr/local/bin/node /usr/local/bin/node
COPY --from=node-base /usr/local/lib/node_modules /usr/local/lib/node_modules

# Create symlinks for npm and npx and ensure they're executable
RUN chmod +x /usr/local/bin/node && \
    ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx && \
    chmod +x /usr/local/bin/npm && \
    chmod +x /usr/local/bin/npx

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy Python project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 tramlines

# Set up directories with proper permissions
RUN mkdir -p /app/logs /app/policies
RUN chown -R tramlines:tramlines /app

USER tramlines

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Default command
CMD ["uv", "run", "tl"] 

