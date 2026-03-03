"""Smoke tests for /v1/analytics endpoints."""
from unittest.mock import AsyncMock, MagicMock


def _mock(rows):
    mock = MagicMock()
    mock.mappings.return_value.all.return_value = rows
    return mock


def test_genero_returns_200(client, mock_db):
    rows = [{"competencia": "2024-01", "sexo": "1", "admissoes": 100,
             "desligamentos": 80, "saldo": 20, "salario_medio": 2500.0}]
    mock_db.execute = AsyncMock(return_value=_mock(rows))
    r = client.get("/v1/analytics/demografico/genero")
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_causas_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_mock([]))
    r = client.get("/v1/analytics/rotatividade/causas")
    assert r.status_code == 200


def test_porte_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_mock([]))
    r = client.get("/v1/analytics/empresa/porte")
    assert r.status_code == 200


def test_ocupacoes_ranking_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_mock([]))
    r = client.get("/v1/analytics/ocupacoes/ranking")
    assert r.status_code == 200
