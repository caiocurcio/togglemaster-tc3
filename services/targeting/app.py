import os

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "targeting")
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
        CREATE TABLE IF NOT EXISTS targeting_rules (
            flag_name VARCHAR(255) PRIMARY KEY,
            rollout_percentage INTEGER NOT NULL DEFAULT 0,
            user_whitelist TEXT[] NOT NULL DEFAULT '{}',
            user_blacklist TEXT[] NOT NULL DEFAULT '{}'
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.cli.command("init-db")
def init_db_command():
    """Cria as tabelas do serviço de targeting (idempotente)."""
    init_db()
    print("Banco de dados do targeting inicializado.")


DEFAULT_RULE = {"rollout_percentage": 0, "user_whitelist": [], "user_blacklist": []}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "targeting"}), 200


@app.route("/targeting/<flag_name>", methods=["GET"])
def get_rule(flag_name):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT flag_name, rollout_percentage, user_whitelist, user_blacklist "
        "FROM targeting_rules WHERE flag_name = %s",
        (flag_name,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        # Sem regra cadastrada = comportamento padrão (sem segmentação)
        return jsonify({"flag_name": flag_name, **DEFAULT_RULE}), 200
    return jsonify(dict(row)), 200


@app.route("/targeting/<flag_name>", methods=["PUT"])
def upsert_rule(flag_name):
    data = request.get_json(silent=True) or {}
    rollout_percentage = int(data.get("rollout_percentage", 0))
    user_whitelist = list(data.get("user_whitelist", []))
    user_blacklist = list(data.get("user_blacklist", []))

    if not 0 <= rollout_percentage <= 100:
        return jsonify({"error": "rollout_percentage deve estar entre 0 e 100"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO targeting_rules (flag_name, rollout_percentage, user_whitelist, user_blacklist)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (flag_name) DO UPDATE
        SET rollout_percentage = EXCLUDED.rollout_percentage,
            user_whitelist = EXCLUDED.user_whitelist,
            user_blacklist = EXCLUDED.user_blacklist
        """,
        (flag_name, rollout_percentage, user_whitelist, user_blacklist),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": f"Regra de targeting para '{flag_name}' salva"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
