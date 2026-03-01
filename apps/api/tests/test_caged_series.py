import json
from unittest.mock import AsyncMock, MagicMock


def _make_mock_result(rows: list) -> MagicMock:
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    return mock_result


def test_series_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))

    r = client.get("/v1/caged/series")
    assert r.status_code == 200
    body = r.json()
    assert "series" in body
    assert "meses" in body
    assert body["meses"] == 12


def test_series_invalid_meses_too_large(client):
    r = client.get("/v1/caged/series?meses=61")
    assert r.status_code == 422


def test_series_invalid_meses_zero(client):
    r = client.get("/v1/caged/series?meses=0")
    assert r.status_code == 422


def test_series_invalid_cnae2_too_long(client):
    r = client.get("/v1/caged/series?cnae2=999")
    assert r.status_code == 422


def test_series_with_filters(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))

    r = client.get("/v1/caged/series?cnae2=47&uf=SP&meses=24")
    assert r.status_code == 200
    body = r.json()
    assert body["meses"] == 24
    assert body["cnae2"] == "47"
    assert body["uf"] == "SP"


def test_series_returns_data_from_db(client, mock_db):
    rows = [
        {
            "competencia": f"2024-{i+1:02d}",
            "admissoes": 100 + i,
            "desligamentos": 80 + i,
            "saldo": 20,
            "salario_medio": 2000.00,
        }
        for i in range(3)
    ]
    mock_db.execute = AsyncMock(return_value=_make_mock_result(rows))

    r = client.get("/v1/caged/series?meses=3")
    assert r.status_code == 200
    body = r.json()
    assert len(body["series"]) == 3
    assert body["series"][0]["competencia"] == "2024-01"


def test_series_cache_hit_skips_db(client, mock_db, mock_redis):
    cached_payload = {
        "series": [],
        "meses": 12,
        "cnae2": None,
        "uf": None,
    }
    mock_redis.get = AsyncMock(return_value=json.dumps(cached_payload))
    mock_db.execute = AsyncMock()

    r = client.get("/v1/caged/series")
    assert r.status_code == 200
    mock_db.execute.assert_not_called()
