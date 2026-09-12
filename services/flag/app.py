import os
import subprocess

import psycopg2
from flask import Flask, jsonify, request


app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "flag")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS flags (
            name VARCHAR(255) PRIMARY KEY,
            is_enabled BOOLEAN NOT NULL DEFAULT false
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.cli.command("init-db")
def init_db_command():
    """Cria as tabelas do serviço de flag (idempotente)."""
    init_db()
    print("Banco de dados do flag inicializado.")


@app.route("/debug/echo")
def debug_echo():
    msg = request.args.get("msg", "")
    subprocess.call(f"echo {msg}", shell=True)  # inseguro de proposito p/ demo do Bandit
    return {"echoed": msg}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "flag"}), 200


@app.route("/flags", methods=["POST"])
def create_flag():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    is_enabled = bool(data.get("is_enabled", False))
    if not name:
        return jsonify({"error": "O campo 'name' é obrigatório"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO flags (name, is_enabled) VALUES (%s, %s)", (name, is_enabled)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": f"Flag '{name}' já existe"}), 409
    finally:
        cur.close()
        conn.close()

    return jsonify({"message": f"Flag '{name}' created successfully"}), 201


@app.route("/flags", methods=["GET"])
def list_flags():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, is_enabled FROM flags ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"name": r[0], "is_enabled": r[1]} for r in rows]), 200


@app.route("/flags/<name>", methods=["GET"])
def get_flag(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, is_enabled FROM flags WHERE name = %s", (name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({"error": f"Flag '{name}' não encontrada"}), 404
    return jsonify({"name": row[0], "is_enabled": row[1]}), 200


@app.route("/flags/<name>", methods=["PUT"])
def update_flag(name):
    data = request.get_json(silent=True) or {}
    if "is_enabled" not in data:
        return jsonify({"error": "O campo 'is_enabled' é obrigatório"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE flags SET is_enabled = %s WHERE name = %s",
        (bool(data["is_enabled"]), name),
    )
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        return jsonify({"error": f"Flag '{name}' não encontrada"}), 404
    return jsonify({"message": f"Flag '{name}' updated"}), 200


if __name__ == "__main__":
    # Usado so em desenvolvimento local (fora do Docker). Em producao quem
    # sobe o servico e' o Gunicorn (ver Dockerfile), nunca este bloco.
    # bind em 0.0.0.0 e' intencional: dentro de um container isso e' o que
    # permite o Kubernetes/Docker alcancar o processo - nao expoe nada que
    # o Service/Ingress do K8s ja nao decida expor.
    app.run(host="0.0.0.0", port=5000)  # nosec B104
