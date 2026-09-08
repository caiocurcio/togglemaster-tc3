import os
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "auth")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_EXPIRES_SECONDS = int(os.environ.get("JWT_EXPIRES_SECONDS", "3600"))


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            name VARCHAR(255) PRIMARY KEY,
            api_key VARCHAR(64) UNIQUE NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.cli.command("init-db")
def init_db_command():
    """Cria as tabelas do serviço de auth (idempotente)."""
    init_db()
    print("Banco de dados do auth inicializado.")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "auth"}), 200


@app.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "O campo 'name' é obrigatório"}), 400

    api_key = secrets.token_hex(24)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO clients (name, api_key) VALUES (%s, %s)", (name, api_key)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": f"Client '{name}' já existe"}), 409
    finally:
        cur.close()
        conn.close()

    return jsonify({"name": name, "api_key": api_key}), 201


@app.route("/token", methods=["POST"])
def issue_token():
    data = request.get_json(silent=True) or {}
    api_key = data.get("api_key")
    if not api_key:
        return jsonify({"error": "O campo 'api_key' é obrigatório"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM clients WHERE api_key = %s", (api_key,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "api_key inválida"}), 401

    client_name = row[0]
    now = datetime.now(timezone.utc)
    payload = {
        "sub": client_name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=JWT_EXPIRES_SECONDS)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return jsonify({"access_token": token, "expires_in": JWT_EXPIRES_SECONDS}), 200


@app.route("/verify", methods=["GET"])
def verify_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Header 'Authorization: Bearer <token>' ausente"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 401

    return jsonify({"valid": True, "claims": claims}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
