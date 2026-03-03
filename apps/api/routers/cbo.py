# apps/api/routers/cbo.py
"""
CBO endpoints — ocupações e grupos CBO.
GET /v1/cbo/occupations — top CBO groups by admissões/saldo
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
from schemas.caged import CBOItem
from services.cache import CacheService

router = APIRouter()
settings = get_settings()


def _make_cache_key(prefix: str, **kwargs: object) -> str:
    content = json.dumps(kwargs, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.md5(content.encode()).hexdigest()[:8]}"


@router.get("/occupations", response_model=list[CBOItem])
async def get_cbo_occupations(
    cnae2: Optional[str] = Query(None, min_length=2, max_length=2),
    uf: Optional[str] = Query(None, min_length=2, max_length=2),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> list[CBOItem]:
    """Top CBO groups by admissões. Cache: 1h."""
    cache_key = _make_cache_key("cbo:occupations", cnae2=cnae2, uf=uf, limit=limit)
    cache_svc = CacheService(redis)
    cached = await cache_svc.get(cache_key)
    if cached:
        return [CBOItem(**item) for item in cached]

    clauses, params = [], {}
    if cnae2:
        clauses.append("f.cnae2 = :cnae2")
        params["cnae2"] = cnae2
    if uf:
        clauses.append("f.uf = :uf")
        params["uf"] = uf
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    sql = text(f"""
        SELECT
            f.cbo6,
            COALESCE(r.descricao, f.cbo6)          AS descricao,
            SUM(f.admissoes)::int                   AS admissoes,
            SUM(f.desligamentos)::int               AS desligamentos,
            SUM(f.admissoes - f.desligamentos)::int AS saldo,
            ROUND(AVG(f.salario_medio)::numeric, 2) AS salario_medio
        FROM fato_caged f
        LEFT JOIN ref_cbo r ON r.cbo6 = f.cbo6
        {where}
        GROUP BY f.cbo6, r.descricao
        ORDER BY admissoes DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    data = [CBOItem(**dict(row)) for row in rows]

    await cache_svc.set(cache_key, [item.model_dump() for item in data], settings.cache_ttl_caged)
    return data
