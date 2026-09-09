from unittest.mock import MagicMock, patch

import psycopg2
import pytest

import app as flag_app


@pytest.fixture
def client():
    flag_app.app.config["TESTING"] = True
    return flag_app.app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "service": "flag"}


def test_create_flag_success(client):
    mock_conn = MagicMock()
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.post("/flags", json={"name": "novo-checkout", "is_enabled": True})
    assert resp.status_code == 201
    mock_conn.commit.assert_called_once()


def test_create_flag_missing_name_returns_400(client):
    resp = client.post("/flags", json={})
    assert resp.status_code == 400


def test_create_flag_duplicate_returns_409(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.execute.side_effect = psycopg2.errors.UniqueViolation()
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.post("/flags", json={"name": "novo-checkout"})
    assert resp.status_code == 409
    mock_conn.rollback.assert_called_once()


def test_list_flags(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchall.return_value = [("flag-a", True), ("flag-b", False)]
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.get("/flags")
    assert resp.status_code == 200
    assert resp.get_json() == [
        {"name": "flag-a", "is_enabled": True},
        {"name": "flag-b", "is_enabled": False},
    ]


def test_get_flag_found(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = ("novo-checkout", True)
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.get("/flags/novo-checkout")
    assert resp.status_code == 200
    assert resp.get_json() == {"name": "novo-checkout", "is_enabled": True}


def test_get_flag_not_found(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = None
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.get("/flags/nao-existe")
    assert resp.status_code == 404


def test_update_flag_success(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.rowcount = 1
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.put("/flags/novo-checkout", json={"is_enabled": False})
    assert resp.status_code == 200


def test_update_flag_missing_field_returns_400(client):
    resp = client.put("/flags/novo-checkout", json={})
    assert resp.status_code == 400


def test_update_flag_not_found_returns_404(client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.rowcount = 0
    with patch("app.get_db_connection", return_value=mock_conn):
        resp = client.put("/flags/nao-existe", json={"is_enabled": True})
    assert resp.status_code == 404
