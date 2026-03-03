"""
Tests for /v1/turnover endpoints.

PW-48 (Fase 2): /benchmark — stub returning [] (CAGED proxy)
PW-49 (Fase 4): /{cnpj} — not implemented, raises 500
"""


def test_benchmark_requires_cnae2(client):
    """cnae2 is required — missing it should return 422."""
    r = client.get("/v1/turnover/benchmark")
    assert r.status_code == 422


def test_benchmark_returns_200_with_cnae2(client):
    r = client.get("/v1/turnover/benchmark?cnae2=47")
    assert r.status_code == 200
    assert r.json() == []


def test_benchmark_accepts_uf_filter(client):
    r = client.get("/v1/turnover/benchmark?cnae2=47&uf=SP")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_benchmark_accepts_period_filters(client):
    r = client.get(
        "/v1/turnover/benchmark?cnae2=47&periodo_inicio=2024-01&periodo_fim=2024-12"
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_cnpj_endpoint_not_implemented(client):
    """PW-49 endpoint raises NotImplementedError until Fase 4 (RAIS ingestão)."""
    import pytest

    with pytest.raises(NotImplementedError, match="PW-49"):
        client.get("/v1/turnover/12345678000195")
