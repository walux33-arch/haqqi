FROM python:3.12-slim

WORKDIR /app

# System deps: OCR + Playwright + healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ara \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN python -m playwright install chromium 2>&1

COPY . .

RUN useradd -m -u 1000 haqqi && chown -R haqqi:haqqi /app
USER haqqi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
