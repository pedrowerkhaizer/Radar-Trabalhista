"""
CAGED endpoints — Monitor de Mercado de Trabalho.
PW-42: API FastAPI endpoints CAGED /summary e /series com Redis cache
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class CAGEDSummary(BaseModel):
    competencia: str
    cnae2: str | None
    uf: str | None
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: float | None


class CAGEDSeries(BaseModel):
    series: list[CAGEDSummary]


@router.get("/summary", response_model=list[CAGEDSummary])
async def get_caged_summary(
    cnae2: str | None = Query(None, description="Código CNAE 2 dígitos"),
    uf: str | None = Query(None, description="Sigla da UF (ex: SP, RJ)"),
    periodo_inicio: str | None = Query(None, description="Competência início (YYYY-MM)"),
    periodo_fim: str | None = Query(None, description="Competência fim (YYYY-MM)"),
) -> list[CAGEDSummary]:
    """
    Retorna resumo de admissões, demissões e saldo por filtros combinados.
    Plano: Free.
    """
    # TODO PW-42: implementar query real no PostgreSQL com cache Redis
    return []


@router.get("/series", response_model=CAGEDSeries)
async def get_caged_series(
    cnae2: str | None = Query(None, description="Código CNAE 2 dígitos"),
    uf: str | None = Query(None, description="Sigla da UF"),
    meses: int = Query(12, ge=1, le=60, description="Quantidade de meses (1-60)"),
) -> CAGEDSeries:
    """
    Retorna série histórica mensal com parâmetros.
    Plano: Free.
    """
    # TODO PW-42: implementar série histórica com cache Redis
    return CAGEDSeries(series=[])
