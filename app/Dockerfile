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



# FROM python:3.11-slim

# # Environment
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# WORKDIR /app

# # System deps
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # 1. Create a non-root user
# # We create a user named 'appuser' and a home directory for them
# RUN useradd -m -u 1000 appuser

# # Install python deps
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy project
# COPY . .

# # 2. Change ownership of the app directory to the new user
# # This is crucial so Celery can write the 'celerybeat-schedule' file
# RUN chown -R appuser:appuser /app

# # 3. Switch from root to the non-root user
# USER appuser

# # Default command (Uvicorn for the web service)
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM python:3.11-slim

# 1. Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# This ensures the virtual environment is used automatically
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 2. Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Create a virtual environment and a non-root user
RUN python -m venv /opt/venv && \
    useradd -m -u 1000 appuser

# 4. Install python dependencies into the virtual environment
# We do this as root so we can write to /opt/venv
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy project and fix permissions
COPY . .
RUN chown -R appuser:appuser /app /opt/venv

# 6. Switch to non-root user
USER appuser

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]