"""
CAGED endpoints — Monitor de Mercado de Trabalho.
PW-42: endpoints com queries reais PostgreSQL + Redis cache
"""

import hashlib
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db import get_db, get_redis
from schemas.caged import (
    CAGEDSeriesResponse,
    CAGEDSummaryItem,
    CAGEDSummaryResponse,
)
from services.cache import CacheService

router = APIRouter()
settings = get_settings()


def _make_cache_key(prefix: str, **kwargs: object) -> str:
    content = json.dumps(kwargs, sort_keys=True, default=str)
    hash_ = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{prefix}:{hash_}"


@router.get("/summary", response_model=CAGEDSummaryResponse)
async def get_caged_summary(
    cnae2: Optional[str] = Query(
        None, min_length=2, max_length=2, description="CNAE 2 dígitos"
    ),
    uf: Optional[str] = Query(
        None, min_length=2, max_length=2, description="Sigla UF"
    ),
    periodo_inicio: Optional[str] = Query(
        None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM"
    ),
    periodo_fim: Optional[str] = Query(
        None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM"
    ),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> CAGEDSummaryResponse:
    """
    Resumo de admissões, demissões e saldo por competência.

    Retorna dados agregados mensais com filtros opcionais.
    Plano: Free. Cache: 1h.
    """
    cache_key = _make_cache_key(
        "caged:summary",
        cnae2=cnae2,
        uf=uf,
        inicio=periodo_inicio,
        fim=periodo_fim,
    )
    cache_svc = CacheService(redis)

    cached = await cache_svc.get(cache_key)
    if cached:
        return CAGEDSummaryResponse(**cached)

    # Construir query com parâmetros nomeados — sem string interpolation
    conditions: list[str] = []
    params: dict[str, object] = {}

    if cnae2:
        conditions.append("cnae2 = :cnae2")
        params["cnae2"] = cnae2
    if uf:
        conditions.append("uf = :uf")
        params["uf"] = uf.upper()
    if periodo_inicio:
        conditions.append("competencia >= :inicio::date")
        params["inicio"] = f"{periodo_inicio}-01"
    if periodo_fim:
        conditions.append("competencia <= :fim::date")
        params["fim"] = f"{periodo_fim}-01"

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = text(f"""
        SELECT
            TO_CHAR(competencia, 'YYYY-MM') AS competencia,
            SUM(admissoes)::int              AS admissoes,
            SUM(desligamentos)::int          AS desligamentos,
            SUM(admissoes - desligamentos)::int AS saldo,
            ROUND(AVG(salario_medio)::numeric, 2) AS salario_medio
        FROM fato_caged
        {where_clause}
        GROUP BY competencia
        ORDER BY competencia DESC
        LIMIT 60
    """)

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    data = [CAGEDSummaryItem(**dict(row)) for row in rows]
    response = CAGEDSummaryResponse(
        data=data,
        total=len(data),
        filtros_aplicados={
            k: v
            for k, v in {
                "cnae2": cnae2,
                "uf": uf,
                "periodo_inicio": periodo_inicio,
                "periodo_fim": periodo_fim,
            }.items()
            if v
        },
    )

    await cache_svc.set(cache_key, response.model_dump(), settings.cache_ttl_caged)

    return response


@router.get("/series", response_model=CAGEDSeriesResponse)
async def get_caged_series(
    cnae2: Optional[str] = Query(None, min_length=2, max_length=2),
    uf: Optional[str] = Query(None, min_length=2, max_length=2),
    meses: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> CAGEDSeriesResponse:
    """Série histórica mensal. Plano: Free. Cache: 1h."""
    cache_key = _make_cache_key("caged:series", cnae2=cnae2, uf=uf, meses=meses)
    cache_svc = CacheService(redis)

    cached = await cache_svc.get(cache_key)
    if cached:
        return CAGEDSeriesResponse(**cached)

    # Nota: :meses não pode ser usado diretamente dentro de INTERVAL em PostgreSQL
    # com asyncpg — usamos cast explícito via parâmetro inteiro
    conditions: list[str] = [
        "competencia >= (CURRENT_DATE - (:meses * INTERVAL '1 month'))::date"
    ]
    params: dict[str, object] = {"meses": meses}

    if cnae2:
        conditions.append("cnae2 = :cnae2")
        params["cnae2"] = cnae2
    if uf:
        conditions.append("uf = :uf")
        params["uf"] = uf.upper()

    where = "WHERE " + " AND ".join(conditions)

    sql = text(f"""
        SELECT
            TO_CHAR(competencia, 'YYYY-MM') AS competencia,
            SUM(admissoes)::int              AS admissoes,
            SUM(desligamentos)::int          AS desligamentos,
            SUM(admissoes - desligamentos)::int AS saldo,
            ROUND(AVG(salario_medio)::numeric, 2) AS salario_medio
        FROM fato_caged
        {where}
        GROUP BY competencia
        ORDER BY competencia ASC
    """)

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    series = [CAGEDSummaryItem(**dict(row)) for row in rows]

    response = CAGEDSeriesResponse(series=series, meses=meses, cnae2=cnae2, uf=uf)
    await cache_svc.set(cache_key, response.model_dump(), settings.cache_ttl_caged)

    return response
