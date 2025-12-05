FROM python:3.12-slim

# Install system dependencies for Cairo and PDF generation
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    pkg-config \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run gunicorn
CMD gunicorn wsgi:app --bind 0.0.0.0:5000

