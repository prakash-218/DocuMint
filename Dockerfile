# The React screens (frontend/), built into static/app; only the built files go into the image below
FROM node:22-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

# Cairo/Pango for PDF rendering; DejaVu has the rupee sign used by the PDF layouts
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_ENV=production
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /build/static/app ./static/app
RUN useradd --create-home app && chown -R app /app
USER app

# Railway sets PORT. Migrations run as the pre-deploy step (.railway/railway.ts).
# (Requests are logged by the app as JSON, so gunicorn's own access log stays off.)
CMD gunicorn wsgi:app --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-2} --threads 4 --timeout 120
