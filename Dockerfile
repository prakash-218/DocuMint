FROM python:3.12-slim

# Install system dependencies for Cairo and PDF generation
RUN apt-get update && apt-get install -y \
    cairo \
    libcairo2-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE $PORT

# Run gunicorn
CMD gunicorn wsgi:app --bind 0.0.0.0:$PORT

