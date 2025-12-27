# AgTools - Professional Crop Consulting System
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly (no TensorFlow for smaller image)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi uvicorn pydantic python-multipart \
    pillow numpy scikit-learn pandas \
    python-jose bcrypt email-validator \
    reportlab openpyxl aiosmtplib \
    requests python-dateutil

# Copy application code
COPY backend/ /app/backend/
COPY database/ /app/database/

# Create directories
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
