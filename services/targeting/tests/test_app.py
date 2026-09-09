from unittest.mock import MagicMock, patch

import pytest

import app as targeting_app


@pytest.fixture
def client():
    targeting_app.app.config["TESTING"] = True
    return targeting_app.app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "service": "targeting"}


def test_get_rule_returns_default_when_not_found(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = None
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.get("/targeting/flag-sem-regra")
    assert resp.status_code == 200
    assert resp.get_json() == {
        "flag_name": "flag-sem-regra",
        "rollout_percentage": 0,
        "user_whitelist": [],
        "user_blacklist": [],
    }


def test_get_rule_returns_saved_rule(client):
    saved = {
        "flag_name": "checkout",
        "rollout_percentage": 50,
        "user_whitelist": ["vip-1"],
        "user_blacklist": [],
    }
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = saved
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.get("/targeting/checkout")
    assert resp.status_code == 200
    assert resp.get_json() == saved


def test_upsert_rule_success(client):
    mock_conn = MagicMock()
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.put(
            "/targeting/checkout",
            json={"rollout_percentage": 25, "user_whitelist": ["vip-1"], "user_blacklist": []},
        )
    assert resp.status_code == 200
    mock_conn.commit.assert_called_once()


def test_upsert_rule_rejects_percentage_out_of_range(client):
    resp = client.put("/targeting/checkout", json={"rollout_percentage": 150})
    assert resp.status_code == 400


def test_upsert_rule_defaults_missing_fields(client):
    mock_conn = MagicMock()
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.put("/targeting/checkout", json={})
    assert resp.status_code == 200
