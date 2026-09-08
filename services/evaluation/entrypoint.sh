#!/bin/sh
set -e

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "Aguardando o Redis em ${REDIS_HOST}:${REDIS_PORT}..."
python3 - <<PY
import os, socket, time
host = os.environ.get("REDIS_HOST", "localhost")
port = int(os.environ.get("REDIS_PORT", "6379"))
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        print("Redis indisponível - aguardando...")
        time.sleep(1)
PY
echo "Redis disponível!"

echo "Iniciando o servidor Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 app:app
