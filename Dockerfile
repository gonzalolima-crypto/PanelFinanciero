# Imagen para desplegar en Fly.io
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DATA_DIR=/data \
    DB_PATH=/data/panel.db \
    UPLOAD_DIR=/data/uploads

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

# El volumen persistente de Fly se monta acá (ver fly.toml)
RUN mkdir -p /data

EXPOSE 8080

# 2 workers alcanza de sobra para uso personal.
# Forma "shell" para que respete la variable PORT que inyecta el hosting.
CMD gunicorn --bind "0.0.0.0:${PORT:-8080}" --workers 2 --timeout 120 wsgi:app
