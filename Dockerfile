# VetClaw - Dockerfile for VPS/Railway Deployment
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV VETCLAW_DB_PATH=/app/data/vetclaw.db

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
