FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    ARTIFACTS_PATH=/app/vitalyx_artifacts \
    APP_ENV=production

WORKDIR /app

RUN groupadd --system vitalyx && useradd --system --gid vitalyx --create-home vitalyx

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY vitalyx_artifacts ./vitalyx_artifacts

RUN chown -R vitalyx:vitalyx /app
USER vitalyx

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8000') + '/health', timeout=3)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
