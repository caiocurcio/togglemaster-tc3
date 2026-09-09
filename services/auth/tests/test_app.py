import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

os.environ.setdefault("JWT_SECRET", "test-secret")

import jwt  # noqa: E402
import psycopg2  # noqa: E402
import pytest  # noqa: E402

import app as auth_app  # noqa: E402


@pytest.fixture
def client():
    auth_app.app.config["TESTING"] = True
    return auth_app.app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "service": "auth"}


def test_create_client_success(client):
    mock_conn = MagicMock()
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.post("/clients", json={"name": "app-mobile"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "app-mobile"
    assert len(body["api_key"]) == 48  # secrets.token_hex(24) -> 48 caracteres hex
    mock_conn.commit.assert_called_once()


def test_create_client_missing_name_returns_400(client):
    resp = client.post("/clients", json={})
    assert resp.status_code == 400


def test_create_client_duplicate_name_returns_409(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.execute.side_effect = psycopg2.errors.UniqueViolation()
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.post("/clients", json={"name": "app-mobile"})
    assert resp.status_code == 409
    mock_conn.rollback.assert_called_once()


def test_issue_token_with_valid_api_key(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = ("app-mobile",)
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.post("/token", json={"api_key": "abc123"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_issue_token_missing_api_key_returns_400(client):
    resp = client.post("/token", json={})
    assert resp.status_code == 400


def test_issue_token_with_invalid_api_key_returns_401(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = None
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.post("/token", json={"api_key": "invalida"})
    assert resp.status_code == 401


def test_verify_valid_token(client):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "app-mobile",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    token = jwt.encode(payload, auth_app.JWT_SECRET, algorithm="HS256")
    resp = client.get("/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True


def test_verify_expired_token_returns_401(client):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "app-mobile",
        "iat": int((now - timedelta(hours=2)).timestamp()),
        "exp": int((now - timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, auth_app.JWT_SECRET, algorithm="HS256")
    resp = client.get("/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_verify_missing_header_returns_401(client):
    resp = client.get("/verify")
    assert resp.status_code == 401
