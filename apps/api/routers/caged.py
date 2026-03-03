"""
CAGED endpoints — Monitor de Mercado de Trabalho.
PW-42: endpoints com queries reais PostgreSQL + Redis cache
"""

import hashlib
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db import get_db, get_redis
from schemas.caged import (
    CAGEDMapItem,
    CAGEDMapResponse,
    CAGEDSeriesResponse,
    CAGEDSummaryItem,
    CAGEDSummaryResponse,
)
from services.cache import CacheService

router = APIRouter()
settings = get_settings()

# Mapeamento sigla UF → código IBGE numérico (como armazenado no banco após ETL)
_UF_IBGE: dict[str, str] = {
    "AC": "12", "AL": "27", "AM": "13", "AP": "16", "BA": "29",
    "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
    "MG": "31", "MS": "50", "MT": "51", "PA": "15", "PB": "25",
    "PE": "26", "PI": "22", "PR": "41", "RJ": "33", "RN": "24",
    "RO": "11", "RR": "14", "RS": "43", "SC": "42", "SE": "28",
    "SP": "35", "TO": "17",
}


def _make_cache_key(prefix: str, **kwargs: object) -> str:
    content = json.dumps(kwargs, sort_keys=True, default=str)
    hash_ = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{prefix}:{hash_}"


def _uf_to_ibge(uf: Optional[str]) -> Optional[str]:
    """Converte sigla UF (ex: 'SP') para código IBGE numérico (ex: '35')."""
    if uf is None:
        return None
    return _UF_IBGE.get(uf.upper())


def _build_where(
    cnae2: Optional[str] = None,
    uf: Optional[str] = None,
    inicio: Optional[str] = None,
    fim: Optional[str] = None,
) -> tuple[str, dict]:
    """Constrói cláusula WHERE dinamicamente para evitar AmbiguousParameterError no asyncpg."""
    clauses: list[str] = []
    params: dict = {}
    if cnae2:
        clauses.append("cnae2 = :cnae2")
        params["cnae2"] = cnae2
    if uf:
        clauses.append("uf = :uf")
        params["uf"] = uf
    if inicio:
        clauses.append("competencia >= CAST(:inicio AS date)")
        params["inicio"] = inicio
    if fim:
        clauses.append("competencia <= CAST(:fim AS date)")
        params["fim"] = fim
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


@router.get("/summary", response_model=CAGEDSummaryResponse)
async def get_caged_summary(
    cnae2: Optional[str] = Query(
        None, min_length=2, max_length=2, description="CNAE 2 dígitos"
    ),
    uf: Optional[str] = Query(
        None, min_length=2, max_length=2, description="Sigla UF (ex: SP)"
    ),
    periodo_inicio: Optional[str] = Query(
        None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM"
    ),
    periodo_fim: Optional[str] = Query(
        None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM"
    ),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CAGEDSummaryResponse:
    """
    Resumo de admissões, demissões e saldo por competência.

    Retorna dados agregados mensais com filtros opcionais.
    Plano: Free. Cache: 1h.
    """
    uf_ibge = _uf_to_ibge(uf)

    cache_key = _make_cache_key(
        "caged:summary",
        cnae2=cnae2,
        uf=uf_ibge,
        inicio=periodo_inicio,
        fim=periodo_fim,
    )
    cache_svc = CacheService(redis)

    cached = await cache_svc.get(cache_key)
    if cached:
        return CAGEDSummaryResponse(**cached)

    where, params = _build_where(
        cnae2=cnae2,
        uf=uf_ibge,
        inicio=f"{periodo_inicio}-01" if periodo_inicio else None,
        fim=f"{periodo_fim}-01" if periodo_fim else None,
    )

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


@router.get("/map", response_model=CAGEDMapResponse)
async def get_caged_map(
    cnae2: Optional[str] = Query(
        None, min_length=2, max_length=2, description="CNAE 2 dígitos"
    ),
    periodo_inicio: Optional[str] = Query(
        None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM"
    ),
    periodo_fim: Optional[str] = Query(
        None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM"
    ),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CAGEDMapResponse:
    """
    Saldo por UF — dados para o mapa coroplético do dashboard.

    Agrega admissões, demissões e saldo por UF (código IBGE 2 dígitos).
    Sem filtro por UF (sempre retorna todas as 27 UFs).
    Cache: 1h.
    """
    cache_key = _make_cache_key(
        "caged:map",
        cnae2=cnae2,
        inicio=periodo_inicio,
        fim=periodo_fim,
    )
    cache_svc = CacheService(redis)

    cached = await cache_svc.get(cache_key)
    if cached:
        return CAGEDMapResponse(**cached)

    where, params = _build_where(
        cnae2=cnae2,
        inicio=f"{periodo_inicio}-01" if periodo_inicio else None,
        fim=f"{periodo_fim}-01" if periodo_fim else None,
    )

    sql = text(f"""
        SELECT
            uf,
            SUM(admissoes)::int                     AS admissoes,
            SUM(desligamentos)::int                 AS desligamentos,
            SUM(admissoes - desligamentos)::int      AS saldo,
            ROUND(AVG(salario_medio)::numeric, 2)   AS salario_medio
        FROM fato_caged
        {where}
        GROUP BY uf
        ORDER BY uf
    """)

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    data = [CAGEDMapItem(**dict(row)) for row in rows]

    response = CAGEDMapResponse(data=data, total=len(data))
    await cache_svc.set(cache_key, response.model_dump(), settings.cache_ttl_caged)

    return response


@router.get("/series", response_model=CAGEDSeriesResponse)
async def get_caged_series(
    cnae2: Optional[str] = Query(None, min_length=2, max_length=2),
    uf: Optional[str] = Query(None, min_length=2, max_length=2),
    meses: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CAGEDSeriesResponse:
    """Série histórica mensal. Plano: Free. Cache: 1h."""
    uf_ibge = _uf_to_ibge(uf)
    cache_key = _make_cache_key("caged:series", cnae2=cnae2, uf=uf_ibge, meses=meses)
    cache_svc = CacheService(redis)

    cached = await cache_svc.get(cache_key)
    if cached:
        return CAGEDSeriesResponse(**cached)

    extra_where, extra_params = _build_where(cnae2=cnae2, uf=uf_ibge)
    extra_clause = ("AND " + extra_where.replace("WHERE ", "")) if extra_where else ""

    sql = text(f"""
        SELECT
            TO_CHAR(competencia, 'YYYY-MM') AS competencia,
            SUM(admissoes)::int              AS admissoes,
            SUM(desligamentos)::int          AS desligamentos,
            SUM(admissoes - desligamentos)::int AS saldo,
            ROUND(AVG(salario_medio)::numeric, 2) AS salario_medio
        FROM fato_caged
        WHERE competencia >= (
            SELECT (MAX(competencia) - INTERVAL '1 month' * :meses)::date FROM fato_caged
        )
        {extra_clause}
        GROUP BY competencia
        ORDER BY competencia ASC
    """)

    params = {"meses": meses, **extra_params}

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    series = [CAGEDSummaryItem(**dict(row)) for row in rows]

    response = CAGEDSeriesResponse(series=series, meses=meses, cnae2=cnae2, uf=uf)
    await cache_svc.set(cache_key, response.model_dump(), settings.cache_ttl_caged)

    return response
