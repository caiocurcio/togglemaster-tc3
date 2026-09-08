#!/bin/sh
set -e

if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_NAME" ]; then
  echo "Erro: DB_HOST, DB_PORT e DB_NAME precisam estar definidos."
  exit 1
fi

echo "Aguardando o banco de dados em ${DB_HOST}:${DB_PORT}..."
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -q -U "$DB_USER"; do
  echo "Banco de dados indisponível - aguardando..."
  sleep 1
done
echo "Banco de dados disponível!"

echo "Inicializando o banco de dados do auth..."
flask init-db

echo "Iniciando o servidor Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 app:app
