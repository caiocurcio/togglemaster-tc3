import json
import os
from unittest.mock import patch

import pytest

os.environ.setdefault("REDIS_HOST", "localhost")

import app as evaluation_app  # noqa: E402  (precisa vir depois do setdefault acima)


class FakeResponse:
    """Substitui requests.Response nos testes, sem precisar de rede de verdade."""

    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


@pytest.fixture
def client():
    evaluation_app.app.config["TESTING"] = True
    return evaluation_app.app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "service": "evaluation"}


def test_decide_disabled_flag_never_enabled():
    rules = {
        "is_enabled": False,
        "rollout_percentage": 100,
        "user_whitelist": [],
        "user_blacklist": [],
    }
    assert evaluation_app.decide(rules, "qualquer-usuario") is False


def test_decide_blacklist_wins_over_whitelist():
    rules = {
        "is_enabled": True,
        "rollout_percentage": 100,
        "user_whitelist": ["user-1"],
        "user_blacklist": ["user-1"],
    }
    assert evaluation_app.decide(rules, "user-1") is False


def test_decide_whitelist_bypasses_rollout():
    rules = {
        "is_enabled": True,
        "rollout_percentage": 0,
        "user_whitelist": ["user-vip"],
        "user_blacklist": [],
    }
    assert evaluation_app.decide(rules, "user-vip") is True


def test_decide_rollout_0_percent_disables_everyone():
    rules = {
        "is_enabled": True,
        "rollout_percentage": 0,
        "user_whitelist": [],
        "user_blacklist": [],
    }
    for user_id in ["a", "b", "c", "qualquer-um"]:
        assert evaluation_app.decide(rules, user_id) is False


def test_decide_rollout_100_percent_enables_everyone():
    rules = {
        "is_enabled": True,
        "rollout_percentage": 100,
        "user_whitelist": [],
        "user_blacklist": [],
    }
    for user_id in ["a", "b", "c", "qualquer-um"]:
        assert evaluation_app.decide(rules, user_id) is True


def test_decide_is_deterministic_for_same_user():
    rules = {
        "is_enabled": True,
        "rollout_percentage": 50,
        "user_whitelist": [],
        "user_blacklist": [],
    }
    first = evaluation_app.decide(rules, "usuario-fixo")
    second = evaluation_app.decide(rules, "usuario-fixo")
    assert first == second


def test_publish_event_is_noop_without_sqs_configured():
    # No ambiente de teste SQS_QUEUE_URL nao esta setada, entao sqs_client e' None
    # e publish_event deve simplesmente retornar sem levantar excecao.
    evaluation_app.publish_event("minha-flag", "user-1", True)


def test_get_flag_and_rules_cache_hit_skips_http_calls():
    cached_payload = {
        "is_enabled": True,
        "rollout_percentage": 50,
        "user_whitelist": [],
        "user_blacklist": [],
    }
    with patch("app.redis_client") as mock_redis, patch("app.requests.get") as mock_get:
        mock_redis.get.return_value = json.dumps(cached_payload)
        result = evaluation_app.get_flag_and_rules("minha-flag")
        assert result == cached_payload
        mock_get.assert_not_called()


def test_get_flag_and_rules_cache_miss_calls_flag_and_targeting_services():
    with patch("app.redis_client") as mock_redis, patch("app.requests.get") as mock_get:
        mock_redis.get.return_value = None
        mock_get.side_effect = [
            FakeResponse(200, {"name": "minha-flag", "is_enabled": True}),
            FakeResponse(
                200, {"rollout_percentage": 30, "user_whitelist": [], "user_blacklist": []}
            ),
        ]
        result = evaluation_app.get_flag_and_rules("minha-flag")
        assert result["is_enabled"] is True
        assert result["rollout_percentage"] == 30
        mock_redis.setex.assert_called_once()


def test_get_flag_and_rules_returns_none_when_flag_not_found():
    with patch("app.redis_client") as mock_redis, patch("app.requests.get") as mock_get:
        mock_redis.get.return_value = None
        mock_get.return_value = FakeResponse(404, {})
        result = evaluation_app.get_flag_and_rules("flag-inexistente")
        assert result is None


def test_evaluate_endpoint_requires_user_id(client):
    resp = client.get("/evaluate/minha-flag")
    assert resp.status_code == 400


def test_evaluate_endpoint_returns_404_for_unknown_flag(client):
    with patch("app.get_flag_and_rules", return_value=None):
        resp = client.get("/evaluate/flag-inexistente?user_id=user-1")
    assert resp.status_code == 404


def test_evaluate_endpoint_happy_path(client):
    rules = {
        "is_enabled": True,
        "rollout_percentage": 100,
        "user_whitelist": [],
        "user_blacklist": [],
    }
    with patch("app.get_flag_and_rules", return_value=rules), patch(
        "app.publish_event"
    ) as mock_publish:
        resp = client.get("/evaluate/minha-flag?user_id=user-1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"flag": "minha-flag", "user_id": "user-1", "enabled": True}
    mock_publish.assert_called_once_with("minha-flag", "user-1", True)
