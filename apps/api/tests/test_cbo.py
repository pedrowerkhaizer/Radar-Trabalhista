"""Tests for GET /v1/cbo/occupations"""
from unittest.mock import AsyncMock, MagicMock


def _make_mock_result(rows):
    mock = MagicMock()
    mock.mappings.return_value.all.return_value = rows
    return mock


def test_cbo_occupations_returns_200(client, mock_db):
    rows = [{"cbo6": "411005", "descricao": "Escriturário", "admissoes": 100,
             "desligamentos": 80, "saldo": 20, "salario_medio": 2500.0}]
    mock_db.execute = AsyncMock(return_value=_make_mock_result(rows))
    r = client.get("/v1/cbo/occupations")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["cbo6"] == "411005"


def test_cbo_occupations_accepts_cnae_filter(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))
    r = client.get("/v1/cbo/occupations?cnae2=47")
    assert r.status_code == 200


def test_cbo_occupations_invalid_cnae(client, mock_db):
    r = client.get("/v1/cbo/occupations?cnae2=999")
    assert r.status_code == 422
