# Google Cloud Run Optimized Dockerfile
# Python 3.11 Slim
FROM python:3.11-slim

WORKDIR /app

# Ensure output is printed directly to Cloud Logging
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and catalog index
COPY . .

# Run FastAPI server with Uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
