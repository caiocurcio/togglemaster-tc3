import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics")

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "ToggleMasterAnalytics")
RUN_CONSUMER = os.environ.get("RUN_CONSUMER", "true").lower() == "true"

sqs_client = boto3.client("sqs", region_name=AWS_REGION) if SQS_QUEUE_URL else None
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

_consumed_count = 0
_consumer_lock = threading.Lock()


def consume_loop():
    """Faz long-polling na fila SQS e grava cada evento no DynamoDB.

    Roda em uma thread de background. Por isso o container deve subir
    com um único worker do Gunicorn (--workers 1): assim existe apenas
    um consumidor por Pod, evitando processar a mesma mensagem em duplicidade.
    """
    global _consumed_count
    if not sqs_client:
        logger.warning("SQS_QUEUE_URL não configurada; consumidor não iniciado.")
        return

    logger.info("Consumidor de analytics iniciado, ouvindo a fila SQS...")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10,
            )
            messages = response.get("Messages", [])
            for message in messages:
                body = json.loads(message["Body"])
                ts = body.get("ts", datetime.now(timezone.utc).isoformat())
                event_id = f"{ts}#{uuid.uuid4()}"
                table.put_item(
                    Item={
                        "flag_name": body["flag_name"],
                        "event_id": event_id,
                        "user_id": body.get("user_id"),
                        "enabled": body.get("enabled"),
                        "ts": body.get("ts"),
                    }
                )
                sqs_client.delete_message(
                    QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"]
                )
                with _consumer_lock:
                    _consumed_count += 1
        except Exception:
            logger.exception("Erro no loop de consumo do SQS; tentando novamente em 5s")
            time.sleep(5)


if RUN_CONSUMER:
    threading.Thread(target=consume_loop, daemon=True).start()


@app.route("/health", methods=["GET"])
def health():
    with _consumer_lock:
        count = _consumed_count
    return jsonify({"status": "ok", "service": "analytics", "events_consumed": count}), 200


@app.route("/analytics/<flag_name>", methods=["GET"])
def get_events(flag_name):
    response = table.query(
        KeyConditionExpression=Key("flag_name").eq(flag_name),
        ScanIndexForward=False,
        Limit=20,
    )
    return jsonify(response.get("Items", [])), 200


if __name__ == "__main__":
    # Usado so em desenvolvimento local (fora do Docker). Em producao quem
    # sobe o servico e' o Gunicorn (ver Dockerfile), nunca este bloco.
    # bind em 0.0.0.0 e' intencional: dentro de um container isso e' o que
    # permite o Kubernetes/Docker alcancar o processo - nao expoe nada que
    # o Service/Ingress do K8s ja nao decida expor.
    app.run(host="0.0.0.0", port=5000)  # nosec B104
