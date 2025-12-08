FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Copy repository into container
COPY . /app

# Set working directory to the temporal folder
WORKDIR /app/temporal-docker/temporal

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential git curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies: temporal-specific and repo requirements
RUN python -m pip install --upgrade pip
RUN if [ -f requirements-temporal.txt ]; then pip install --no-cache-dir -r requirements-temporal.txt; fi
RUN if [ -f ../../requirements.txt ]; then pip install --no-cache-dir -r ../../requirements.txt || true; fi

# Ensure worker script is executable
CMD ["python", "worker.py"]
