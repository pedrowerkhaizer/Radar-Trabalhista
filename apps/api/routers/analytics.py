# apps/api/routers/analytics.py
"""
Analytics endpoints — Demográfico, Rotatividade, Empresa modules.
Prefix: /v1/analytics
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
from routers.caged import _build_where, _uf_to_ibge
from schemas.analytics import (
    CausaDesligamentoItem,
    CausaDesligamentoResponse,
    EscolaridadeItem,
    EscolaridadeResponse,
    FaixaEtariaItem,
    FaixaEtariaResponse,
    GeneroItem,
    GeneroResponse,
    OcupacaoRankingItem,
    OcupacaoRankingResponse,
    PorteEmpresaItem,
    PorteEmpresaResponse,
    TempoEmpregoItem,
    TempoEmpregoResponse,
    TipoVinculoItem,
    TipoVinculoResponse,
)
from services.cache import CacheService

router = APIRouter()
settings = get_settings()

STALE = settings.cache_ttl_caged  # 1h


def _ck(prefix: str, **kw: object) -> str:
    return f"{prefix}:{hashlib.md5(json.dumps(kw, sort_keys=True, default=str).encode()).hexdigest()[:8]}"


# ── Shared query params ───────────────────────────────────────────────────────

def _common_params(
    cnae2: Optional[str] = Query(None, min_length=2, max_length=2),
    uf: Optional[str] = Query(None, min_length=2, max_length=2),
    periodo_inicio: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    periodo_fim: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
) -> dict:
    return dict(cnae2=cnae2, uf=uf, periodo_inicio=periodo_inicio, periodo_fim=periodo_fim)


# ── Demográfico ───────────────────────────────────────────────────────────────

@router.get("/demografico/genero", response_model=GeneroResponse)
async def get_genero(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> GeneroResponse:
    """Admissões/demissões por sexo ao longo do tempo. Cache: 1h."""
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:genero", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return GeneroResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT TO_CHAR(competencia,'YYYY-MM') AS competencia,
               sexo,
               SUM(admissoes)::int AS admissoes,
               SUM(desligamentos)::int AS desligamentos,
               SUM(saldo)::int AS saldo,
               ROUND(AVG(salario_medio)::numeric,2) AS salario_medio
        FROM fato_caged_demog {where}
        GROUP BY competencia, sexo
        ORDER BY competencia ASC, sexo
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [GeneroItem(**dict(r)) for r in rows]
    resp = GeneroResponse(data=data, total=len(data))
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


@router.get("/demografico/escolaridade", response_model=EscolaridadeResponse)
async def get_escolaridade(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> EscolaridadeResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:escolaridade", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return EscolaridadeResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT grau_instrucao,
               SUM(admissoes)::int AS admissoes,
               SUM(desligamentos)::int AS desligamentos,
               SUM(saldo)::int AS saldo,
               ROUND(AVG(salario_medio)::numeric,2) AS salario_medio
        FROM fato_caged_demog {where}
        GROUP BY grau_instrucao ORDER BY grau_instrucao
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [EscolaridadeItem(**dict(r)) for r in rows]
    resp = EscolaridadeResponse(data=data)
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


@router.get("/demografico/faixa-etaria", response_model=FaixaEtariaResponse)
async def get_faixa_etaria(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> FaixaEtariaResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:faixa_etaria", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return FaixaEtariaResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT faixa_etaria,
               SUM(admissoes)::int AS admissoes,
               SUM(desligamentos)::int AS desligamentos,
               SUM(saldo)::int AS saldo
        FROM fato_caged_demog {where}
        GROUP BY faixa_etaria
        ORDER BY faixa_etaria
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [FaixaEtariaItem(**dict(r)) for r in rows]
    resp = FaixaEtariaResponse(data=data)
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


# ── Rotatividade ─────────────────────────────────────────────────────────────

@router.get("/rotatividade/causas", response_model=CausaDesligamentoResponse)
async def get_causas(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CausaDesligamentoResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:causas", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return CausaDesligamentoResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT causa_desligamento,
               SUM(desligamentos)::int AS desligamentos,
               ROUND(AVG(salario_medio)::numeric,2) AS salario_medio
        FROM fato_caged_rotat {where}
        GROUP BY causa_desligamento ORDER BY desligamentos DESC
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [CausaDesligamentoItem(**dict(r)) for r in rows]
    resp = CausaDesligamentoResponse(data=data)
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


@router.get("/rotatividade/tempo-emprego", response_model=TempoEmpregoResponse)
async def get_tempo_emprego(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TempoEmpregoResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:tempo_emprego", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return TempoEmpregoResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT faixa_tempo_emprego, SUM(desligamentos)::int AS desligamentos
        FROM fato_caged_rotat {where}
        GROUP BY faixa_tempo_emprego ORDER BY desligamentos DESC
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [TempoEmpregoItem(**dict(r)) for r in rows]
    resp = TempoEmpregoResponse(data=data)
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


@router.get("/rotatividade/tipo-vinculo", response_model=TipoVinculoResponse)
async def get_tipo_vinculo_rotat(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TipoVinculoResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:vinculo_rotat", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return TipoVinculoResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT tipo_vinculo,
               0 AS admissoes,
               SUM(desligamentos)::int AS desligamentos,
               -SUM(desligamentos)::int AS saldo
        FROM fato_caged_rotat {where}
        GROUP BY tipo_vinculo ORDER BY desligamentos DESC
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [TipoVinculoItem(**dict(r)) for r in rows]
    resp = TipoVinculoResponse(data=data)
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


# ── Ocupações ─────────────────────────────────────────────────────────────────

@router.get("/ocupacoes/ranking", response_model=OcupacaoRankingResponse)
async def get_ocupacoes_ranking(
    p: dict = Depends(_common_params),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OcupacaoRankingResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:ocup_ranking", **p, uf_ibge=uf_ibge, limit=limit)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return OcupacaoRankingResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT
            SUBSTR(f.cbo6, 1, 2) AS cbo_grupo,
            MAX(r.descricao)     AS descricao,
            SUM(f.admissoes)::int AS admissoes,
            SUM(f.desligamentos)::int AS desligamentos,
            SUM(f.admissoes - f.desligamentos)::int AS saldo,
            ROUND(AVG(f.salario_medio)::numeric,2) AS salario_medio
        FROM fato_caged f
        LEFT JOIN ref_cbo r ON SUBSTR(r.cbo6,1,2) = SUBSTR(f.cbo6,1,2)
        {where}
        GROUP BY SUBSTR(f.cbo6,1,2)
        ORDER BY admissoes DESC
        LIMIT :limit
    """)
    params["limit"] = limit
    rows = (await db.execute(sql, params)).mappings().all()
    data = [OcupacaoRankingItem(**dict(r)) for r in rows]
    resp = OcupacaoRankingResponse(data=data, total=len(data))
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


@router.get("/ocupacoes/salario", response_model=OcupacaoRankingResponse)
async def get_ocupacoes_salario(
    p: dict = Depends(_common_params),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OcupacaoRankingResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:ocup_salario", **p, uf_ibge=uf_ibge, limit=limit)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return OcupacaoRankingResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT
            SUBSTR(f.cbo6, 1, 2) AS cbo_grupo,
            MAX(r.descricao)     AS descricao,
            SUM(f.admissoes)::int AS admissoes,
            SUM(f.desligamentos)::int AS desligamentos,
            SUM(f.admissoes - f.desligamentos)::int AS saldo,
            ROUND(AVG(f.salario_medio)::numeric,2) AS salario_medio
        FROM fato_caged f
        LEFT JOIN ref_cbo r ON SUBSTR(r.cbo6,1,2) = SUBSTR(f.cbo6,1,2)
        {where}
        GROUP BY SUBSTR(f.cbo6,1,2)
        ORDER BY salario_medio DESC NULLS LAST
        LIMIT :limit
    """)
    params["limit"] = limit
    rows = (await db.execute(sql, params)).mappings().all()
    data = [OcupacaoRankingItem(**dict(r)) for r in rows]
    resp = OcupacaoRankingResponse(data=data, total=len(data))
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


# ── Empresa ───────────────────────────────────────────────────────────────────

@router.get("/empresa/porte", response_model=PorteEmpresaResponse)
async def get_porte_empresa(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> PorteEmpresaResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:porte", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return PorteEmpresaResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT porte_empresa,
               SUM(admissoes)::int AS admissoes,
               SUM(desligamentos)::int AS desligamentos,
               SUM(saldo)::int AS saldo,
               ROUND(AVG(salario_medio)::numeric,2) AS salario_medio
        FROM fato_caged_empresa {where}
        GROUP BY porte_empresa ORDER BY porte_empresa
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [PorteEmpresaItem(**dict(r)) for r in rows]
    resp = PorteEmpresaResponse(data=data)
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp


@router.get("/empresa/tipo-vinculo", response_model=TipoVinculoResponse)
async def get_tipo_vinculo_empresa(
    p: dict = Depends(_common_params),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TipoVinculoResponse:
    uf_ibge = _uf_to_ibge(p["uf"])
    cache_key = _ck("analytics:vinculo_empresa", **p, uf_ibge=uf_ibge)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return TipoVinculoResponse(**cached)

    where, params = _build_where(
        cnae2=p["cnae2"], uf=uf_ibge,
        inicio=f"{p['periodo_inicio']}-01" if p["periodo_inicio"] else None,
        fim=f"{p['periodo_fim']}-01" if p["periodo_fim"] else None,
    )
    sql = text(f"""
        SELECT tipo_vinculo,
               SUM(admissoes)::int AS admissoes,
               SUM(desligamentos)::int AS desligamentos,
               SUM(saldo)::int AS saldo
        FROM fato_caged_empresa {where}
        GROUP BY tipo_vinculo ORDER BY admissoes DESC
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    data = [TipoVinculoItem(**dict(r)) for r in rows]
    resp = TipoVinculoResponse(data=data)
    await cache_svc.set(cache_key, resp.model_dump(), STALE)
    return resp
