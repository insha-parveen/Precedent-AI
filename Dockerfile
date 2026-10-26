# FastAPI backend for Precedent - Local development container
# Build: docker build -t precedent-api .
# Run: docker run -p 8000:8000 --env-file .env precedent-api

FROM python:3.11-slim

# Set working directory
WORKDIR /app
ENV PYTHONPATH=/app/src

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY db/ ./db/
COPY skills/ ./skills/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "precedent.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
