from unittest.mock import AsyncMock, MagicMock


def _make_mock_result(rows: list) -> MagicMock:
    """Build a mock SQLAlchemy result that supports .mappings().all()."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    return mock_result


def test_summary_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))

    r = client.get("/v1/caged/summary")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    assert "total" in body
    assert body["total"] == 0


def test_summary_invalid_cnae2_too_long(client):
    r = client.get("/v1/caged/summary?cnae2=123")
    assert r.status_code == 422


def test_summary_invalid_uf_too_long(client):
    r = client.get("/v1/caged/summary?uf=SPX")
    assert r.status_code == 422


def test_summary_with_valid_filters(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))

    r = client.get(
        "/v1/caged/summary?cnae2=47&uf=SP&periodo_inicio=2024-01&periodo_fim=2024-12"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["filtros_aplicados"]["cnae2"] == "47"
    assert body["filtros_aplicados"]["uf"] == "SP"


def test_summary_returns_data_from_db(client, mock_db):
    row = MagicMock()
    row.__iter__ = MagicMock(
        return_value=iter(
            [
                ("competencia", "2025-01"),
                ("admissoes", 150),
                ("desligamentos", 100),
                ("saldo", 50),
                ("salario_medio", 2500.00),
            ]
        )
    )
    # mappings().all() must return mapping-like objects; use plain dicts
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {
            "competencia": "2025-01",
            "admissoes": 150,
            "desligamentos": 100,
            "saldo": 50,
            "salario_medio": 2500.00,
        }
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)

    r = client.get("/v1/caged/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["data"][0]["competencia"] == "2025-01"
    assert body["data"][0]["admissoes"] == 150
    assert body["data"][0]["saldo"] == 50


def test_summary_cache_hit_returns_200(client, mock_db, mock_redis):
    """When cache returns a valid payload, DB should not be called."""
    import json

    cached_payload = {
        "data": [],
        "total": 0,
        "filtros_aplicados": {},
    }
    mock_redis.get = AsyncMock(return_value=json.dumps(cached_payload))
    mock_db.execute = AsyncMock()

    r = client.get("/v1/caged/summary")
    assert r.status_code == 200
    mock_db.execute.assert_not_called()
