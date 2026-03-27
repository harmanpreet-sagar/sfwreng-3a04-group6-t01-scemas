# Backend API Dockerfile
# Creates containerized FastAPI application for the Threshold Management System

# Use Python 3.11 slim image for smaller container size
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy dependency file first to leverage Docker layer caching
# Dependencies only rebuild if requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose FastAPI port for external access
EXPOSE 8000

# Start Uvicorn ASGI server with hot-reload for development
# Note: Remove --reload flag in production for better performance
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
