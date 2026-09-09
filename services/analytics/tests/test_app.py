import importlib
import os

os.environ["RUN_CONSUMER"] = "false"  # nao inicia a thread de consumo do SQS durante os testes
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("DYNAMODB_TABLE", "ToggleMasterAnalyticsTest")

import boto3  # noqa: E402
import pytest  # noqa: E402
from moto import mock_aws  # noqa: E402


@pytest.fixture
def app_module():
    """Sobe um DynamoDB fake (moto) com a MESMA chave (flag_name/event_id) da
    tabela real, e (re)importa o app dentro do mock pra garantir que o
    `boto3.resource("dynamodb")` do modulo aponte pro DynamoDB fake, nao pra AWS de verdade."""
    with mock_aws():
        ddb_client = boto3.client("dynamodb", region_name="us-east-1")
        ddb_client.create_table(
            TableName=os.environ["DYNAMODB_TABLE"],
            KeySchema=[
                {"AttributeName": "flag_name", "KeyType": "HASH"},
                {"AttributeName": "event_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "flag_name", "AttributeType": "S"},
                {"AttributeName": "event_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        import app as analytics_app

        importlib.reload(analytics_app)
        yield analytics_app


@pytest.fixture
def client(app_module):
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["service"] == "analytics"
    assert body["events_consumed"] == 0


def test_get_events_empty_when_no_items(client):
    resp = client.get("/analytics/flag-sem-eventos")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_events_returns_items_from_dynamodb(app_module, client):
    app_module.table.put_item(
        Item={
            "flag_name": "checkout",
            "event_id": "2026-01-01T00:00:00#abc",
            "user_id": "user-1",
            "enabled": True,
            "ts": "2026-01-01T00:00:00",
        }
    )
    resp = client.get("/analytics/checkout")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 1
    assert items[0]["user_id"] == "user-1"
    assert items[0]["enabled"] is True
