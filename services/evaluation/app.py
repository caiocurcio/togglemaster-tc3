import hashlib
import json
import logging
import os
from datetime import datetime, timezone

import boto3
import redis
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluation")

FLAG_SERVICE_URL = os.environ.get("FLAG_SERVICE_URL", "http://flag:5000")
TARGETING_SERVICE_URL = os.environ.get("TARGETING_SERVICE_URL", "http://targeting:5000")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "30"))

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
sqs_client = boto3.client("sqs", region_name=AWS_REGION) if SQS_QUEUE_URL else None


def get_flag_and_rules(flag_name):
    """Busca flag + regra de targeting, usando o Redis como cache-aside."""
    cache_key = f"flag:{flag_name}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    flag_resp = requests.get(f"{FLAG_SERVICE_URL}/flags/{flag_name}", timeout=5)
    if flag_resp.status_code == 404:
        return None
    flag_resp.raise_for_status()
    flag_data = flag_resp.json()

    rule_resp = requests.get(f"{TARGETING_SERVICE_URL}/targeting/{flag_name}", timeout=5)
    rule_resp.raise_for_status()
    rule_data = rule_resp.json()

    combined = {
        "is_enabled": flag_data["is_enabled"],
        "rollout_percentage": rule_data.get("rollout_percentage", 0),
        "user_whitelist": rule_data.get("user_whitelist", []),
        "user_blacklist": rule_data.get("user_blacklist", []),
    }
    redis_client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(combined))
    return combined


def decide(flag_and_rules, user_id):
    if not flag_and_rules["is_enabled"]:
        return False
    if user_id in flag_and_rules["user_blacklist"]:
        return False
    if user_id in flag_and_rules["user_whitelist"]:
        return True
    bucket = int(hashlib.md5(user_id.encode("utf-8")).hexdigest(), 16) % 100
    return bucket < flag_and_rules["rollout_percentage"]


def publish_event(flag_name, user_id, enabled):
    if not sqs_client:
        return
    try:
        sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "flag_name": flag_name,
                    "user_id": user_id,
                    "enabled": enabled,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
            ),
        )
    except Exception:
        # A avaliação não deve falhar por causa da fila de analytics.
        logger.exception("Falha ao publicar evento de avaliação no SQS")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "evaluation"}), 200


@app.route("/evaluate/<flag_name>", methods=["GET"])
def evaluate(flag_name):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "O parâmetro 'user_id' é obrigatório"}), 400

    flag_and_rules = get_flag_and_rules(flag_name)
    if flag_and_rules is None:
        return jsonify({"error": f"Flag '{flag_name}' não encontrada"}), 404

    enabled = decide(flag_and_rules, user_id)
    publish_event(flag_name, user_id, enabled)

    return jsonify({"flag": flag_name, "user_id": user_id, "enabled": enabled}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
