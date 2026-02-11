# FROM python:3.11-slim

# # Environment
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# WORKDIR /app

# # System deps
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Install python deps
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy project
# COPY . .

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]



FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1. Create a non-root user
# We create a user named 'appuser' and a home directory for them
RUN useradd -m -u 1000 appuser

# Install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# 2. Change ownership of the app directory to the new user
# This is crucial so Celery can write the 'celerybeat-schedule' file
RUN chown -R appuser:appuser /app

# 3. Switch from root to the non-root user
USER appuser

# Default command (Uvicorn for the web service)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]