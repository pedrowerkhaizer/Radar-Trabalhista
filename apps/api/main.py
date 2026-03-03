from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import analytics, caged, cbo, health, turnover

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup — warm up Redis singleton to avoid cold-start race condition
    from db import get_redis
    await get_redis()
    yield
    # shutdown — dispose DB pool and close Redis
    try:
        from db import engine, redis_client

        await engine.dispose()
        if redis_client:
            await redis_client.aclose()
    except Exception:
        pass


app = FastAPI(
    title="Radar Trabalhista API",
    description="Plataforma de Inteligência em Mercado de Trabalho e Compliance Trabalhista",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(caged.router, prefix="/v1/caged", tags=["CAGED"])
app.include_router(turnover.router, prefix="/v1/turnover", tags=["Turnover"])
app.include_router(cbo.router, prefix="/v1/cbo", tags=["CBO"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
