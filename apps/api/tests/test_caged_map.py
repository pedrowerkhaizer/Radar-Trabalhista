import json
from unittest.mock import AsyncMock, MagicMock


def _make_mock_result(rows: list) -> MagicMock:
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    return mock_result


def test_map_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))

    r = client.get("/v1/caged/map")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    assert "total" in body
    assert body["total"] == 0


def test_map_invalid_cnae2_too_long(client):
    r = client.get("/v1/caged/map?cnae2=999")
    assert r.status_code == 422


def test_map_invalid_periodo_format(client):
    r = client.get("/v1/caged/map?periodo_inicio=2024/01")
    assert r.status_code == 422


def test_map_with_cnae2_filter(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))

    r = client.get("/v1/caged/map?cnae2=47")
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_map_returns_all_ufs(client, mock_db):
    """Map endpoint should aggregate all 27 UFs."""
    rows = [
        {
            "uf": str(code),
            "admissoes": 1000 + i,
            "desligamentos": 800 + i,
            "saldo": 200,
            "salario_medio": 2500.00,
        }
        for i, code in enumerate(
            [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 29,
             31, 32, 33, 35, 41, 42, 43, 50, 51, 52, 53]
        )
    ]
    mock_db.execute = AsyncMock(return_value=_make_mock_result(rows))

    r = client.get("/v1/caged/map")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 27
    assert all("uf" in item for item in body["data"])
    assert all("saldo" in item for item in body["data"])


def test_map_data_structure(client, mock_db):
    """Each map item must have: uf, admissoes, desligamentos, saldo, salario_medio."""
    row = {
        "uf": "35",
        "admissoes": 50000,
        "desligamentos": 40000,
        "saldo": 10000,
        "salario_medio": 3200.50,
    }
    mock_db.execute = AsyncMock(return_value=_make_mock_result([row]))

    r = client.get("/v1/caged/map")
    assert r.status_code == 200
    item = r.json()["data"][0]
    assert item["uf"] == "35"
    assert item["admissoes"] == 50000
    assert item["desligamentos"] == 40000
    assert item["saldo"] == 10000
    assert item["salario_medio"] == 3200.50


def test_map_with_period_filter(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))

    r = client.get("/v1/caged/map?periodo_inicio=2024-01&periodo_fim=2024-12")
    assert r.status_code == 200


def test_map_cache_hit_skips_db(client, mock_db, mock_redis):
    """When cache returns a valid payload, DB should not be called."""
    cached_payload = {"data": [], "total": 0}
    mock_redis.get = AsyncMock(return_value=json.dumps(cached_payload))
    mock_db.execute = AsyncMock()

    r = client.get("/v1/caged/map")
    assert r.status_code == 200
    mock_db.execute.assert_not_called()
