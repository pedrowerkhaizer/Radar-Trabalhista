from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import caged, health, turnover


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup — nothing required; connections are lazy
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(caged.router, prefix="/v1/caged", tags=["CAGED"])
app.include_router(turnover.router, prefix="/v1/turnover", tags=["Turnover"])
