FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-jdk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/src /app/data /app/logs /app/spark/apps /app/spark/data

# Copy application code
COPY src/ /app/src/
COPY spark/ /app/spark/

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "/app/src/main.py"] 