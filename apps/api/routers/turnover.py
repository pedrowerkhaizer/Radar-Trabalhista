"""
Turnover endpoints — Benchmarking de Turnover Setorial.

PW-48 (Fase 2): endpoint beta /v1/turnover/benchmark via CAGED (volume absoluto)
PW-49 (Fase 4): endpoint /v1/turnover/{cnpj} com percentis reais via RAIS
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class TurnoverBenchmarkResponse(BaseModel):
    cnae2: str
    uf: str | None
    periodo_inicio: str
    periodo_fim: str
    desligamentos_sem_justa_causa: int
    desligamentos_a_pedido: int
    total_desligamentos: int
    nota_metodologica: str


class TurnoverPercentilResponse(BaseModel):
    cnpj: str
    cnae2: str
    turnover_estimado: float | None
    percentil: float | None
    classificacao: str | None  # abaixo_media / na_media / acima / critico
    ano_base: int | None
    benchmark: dict  # {p25, p50, p75, p90}
    nota_metodologica: str


@router.get("/benchmark", response_model=list[TurnoverBenchmarkResponse])
async def get_turnover_benchmark(
    cnae2: str = Query(..., description="Código CNAE 2 dígitos (obrigatório)"),
    uf: str | None = Query(None, description="Sigla da UF"),
    periodo_inicio: str | None = Query(None, description="Período início YYYY-MM"),
    periodo_fim: str | None = Query(None, description="Período fim YYYY-MM"),
) -> list[TurnoverBenchmarkResponse]:
    """
    Retorna volume de desligamentos por setor como proxy de turnover (beta).

    NOTA: Esta é a versão beta (Fase 2) usando apenas CAGED.
    Os percentis reais (P25/P50/P75/P90) baseados no estoque RAIS
    serão disponibilizados na Fase 4 (PW-49).

    Plano: Free.
    """
    # TODO PW-48: implementar query em fato_caged filtrando desligamentos sem justa causa
    # e a pedido do empregado, agrupado por cnae2 e UF
    return []


@router.get("/{cnpj}", response_model=TurnoverPercentilResponse)
async def get_turnover_by_cnpj(
    cnpj: str,
) -> TurnoverPercentilResponse:
    """
    Retorna a posição percentil do CNPJ no benchmark setorial.

    Requer RAIS ingerida (mart_turnover_setorial pré-calculado via dbt).
    Implementado na Fase 4 (PW-49).

    Plano: Pro.
    """
    # TODO PW-49: implementar lookup no mart_turnover_setorial
    # e cálculo do percentil do CNPJ via CAGED dos últimos 12 meses / headcount declarado
    raise NotImplementedError("PW-49 (Fase 4): endpoint disponível após ingestão da RAIS")
