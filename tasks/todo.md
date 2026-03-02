# Radar Trabalhista — Task Tracker

Última atualização: 2026-03-02

---

## Fase 1 — Fundação | Meta: 2026-04-12

### PW-40: Infra — Docker Compose + PostgreSQL + TimescaleDB + CI ✅ Done
- [x] Monorepo estruturado (`apps/api`, `apps/web`, `etl/`, `dbt/`, `infra/`)
- [x] `infra/docker-compose.yml` — postgres, redis, api, web, prefect
- [x] `infra/init.sql` — schema completo (fato_caged, compliance_score, users, api_keys, mart_turnover_setorial, refs)
- [x] `.github/workflows/ci.yml` — lint (ruff + eslint), mypy + tsc, pytest
- [x] `Makefile` com targets: up, down, logs, migrate, test, lint, dbt-run
- [x] `.gitignore` + `.env.example` documentados
- [x] `apps/api/Dockerfile` — multi-stage, non-root appuser, healthcheck
- [x] `apps/web/Dockerfile` — multi-stage, non-root nextjs, standalone output
- [x] **[BUG CRÍTICO]** `infra/init.sql`: remover `PARTITION BY RANGE (competencia)` — incompatível com `create_hypertable` do TimescaleDB → docker-compose up falha no init
- [x] **[MAJOR]** `infra/docker-compose.yml`: adicionar healthcheck ao serviço `api` e mudar `web.depends_on.api` para `condition: service_healthy`
- [x] **[MINOR]** `infra/docker-compose.yml`: mover Prefect para banco separado (não compartilhar `radar_trabalhista` com a aplicação)
- [ ] Testar `docker-compose up` end-to-end localmente (requer `make up` com Supabase + Redis ativos)

---

### PW-41: Pipeline ETL CAGED ✅ Done (5/5 testes passando)
- [x] `etl/tasks/download.py` — httpx streaming, py7zr, idempotência por glob
- [x] `etl/tasks/validate.py` — Pandera schema (strict=False), linha count, encoding detection
- [x] `etl/tasks/transform.py` — DuckDB VIEW lazy scan → Parquet zstd
- [x] `etl/tasks/load.py` — psycopg3 COPY, DELETE+COPY atômico (idempotente)
- [x] `etl/flows/caged_flow.py` — orquestração Prefect, retry=2, Slack/email notify
- [x] `etl/tests/test_transform.py` — 5 testes unitários DuckDB SQL
- [x] Schedule cron: `0 8 20-31 * *` (dias 20-31 de cada mês, 08h UTC)
- [x] `dbt/models/staging/stg_caged.sql`
- [x] `dbt/models/marts/mart_mercado_trabalho.sql`
- [x] **[CRÍTICO]** `etl/tasks/transform.py`: validar e canonicalizar `csv_path` antes de interpolar em f-string SQL do DuckDB (path vem de parâmetro do flow → risco de path traversal)
- [x] **[MAJOR]** `etl/tasks/validate.py`: capturar também `pa.errors.SchemaError` (singular) além de `SchemaErrors` — sem isso schema errors não-lazy podem bloquear o pipeline
- [x] **[MINOR]** `etl/tasks/download.py`: usar `datetime.now(timezone.utc)` em vez de `datetime.now()` no `_detect_latest_competencia()`
- [x] **[MINOR]** `etl/tests/test_transform.py`: extraído `AGGREGATION_SQL_CORE` + `AGGREGATION_COLUMNS` como constantes em `transform.py`; testes usam import direto — sem duplicação
- [ ] Carregar 12 meses históricos (backfill manual — ver instruções abaixo)
- [ ] Testar flow completo com arquivo real do PDET

---

### PW-42: API FastAPI — CAGED endpoints + Redis cache ✅ Done (15/15 testes passando)
- [x] `apps/api/config.py` — Pydantic BaseSettings com `@lru_cache`
- [x] `apps/api/db.py` — SQLAlchemy async engine (asyncpg), pool_size=10/max_overflow=20
- [x] `apps/api/db.py` — Redis singleton `get_redis()`
- [x] `apps/api/services/cache.py` — CacheService (get/set/delete_pattern)
- [x] `apps/api/schemas/caged.py` — Pydantic v2 (CAGEDSummaryItem, CAGEDSummaryResponse, CAGEDSeriesResponse)
- [x] `apps/api/routers/caged.py` — GET /v1/caged/summary + /v1/caged/series com cache Redis 1h
- [x] `apps/api/routers/health.py` — GET /health
- [x] `apps/api/main.py` — FastAPI + lifespan (dispose engine + close redis on shutdown)
- [x] `apps/api/tests/` — 15 testes (conftest + dependency_overrides + 3 test files)
- [x] **[CRÍTICO]** `apps/api/db.py`: race condition no Redis singleton — múltiplas coroutines podem criar pools simultâneos no cold start; warmup do singleton no lifespan startup resolve
- [x] **[CRÍTICO]** `apps/api/routers/caged.py`: `where_clause` é interpolado via f-string em `text()` — reestruturar para SQL estático com guards `(:param IS NULL OR col = :param)` eliminando f-string SQL
- [x] **[MAJOR]** `apps/api/services/cache.py`: substituir `KEYS pattern` (O(N) bloqueante) por cursor SCAN no `delete_pattern()`
- [x] **[MAJOR]** `apps/api/main.py`: CORS origins para Settings (não hardcoded); `allow_methods` restringir a `["GET"]`; `allow_headers` restringir
- [x] **[MINOR]** `apps/api/routers/caged.py`: anotar tipo do parâmetro `redis` → `redis: Redis = Depends(get_redis)`
- [x] **[MINOR-10 / BUG]** `apps/api/routers/caged.py`: filtro `uf` recebe sigla (ex: "SP") mas banco armazena código numérico IBGE (ex: "35") — adicionar mapping dict sigla→código antes do `params["uf"]`
- [ ] Swagger UI acessível em `/docs` (verificar após `make up`)
- [ ] Testar P95 < 500ms com dados reais (requer backfill CAGED)

---

### PW-43: Frontend Next.js — Landing + Dashboard + KPIs + CAGEDChart + FilterBar ✅ Done (build clean)
- [x] Next.js 14 App Router + TypeScript + Tailwind CSS + shadcn/ui
- [x] `src/lib/types.ts` — interfaces TypeScript (CAGEDSummaryItem, FilterState, constantes CNAE/UF)
- [x] `src/lib/api-client.ts` — fetch tipado, timeout 10s, buildParams
- [x] `src/store/filters.ts` — Zustand store tipado com `setFilter<K extends keyof FilterState>`
- [x] `src/hooks/useCaged.ts` — TanStack Query v5 (useCagedSummary + useCagedSeries)
- [x] `src/app/providers.tsx` — QueryClientProvider (client component)
- [x] `src/app/layout.tsx` — RootLayout, Inter font, lang=pt-BR
- [x] `src/app/page.tsx` — Landing SSG com 3 feature cards
- [x] `src/app/dashboard/page.tsx` — Dashboard com KPIs, gráfico, mapa, ranking
- [x] `src/app/dashboard/loading.tsx` — Skeleton layout
- [x] `src/app/dashboard/error.tsx` — Error boundary com retry
- [x] `src/components/KPICard.tsx` — sparkline, trend badge, skeleton
- [x] `src/components/FilterBar.tsx` — selects CNAE/UF/período + URL sync
- [x] `src/components/CAGEDChart.tsx` — ComposedChart (barras + linha saldo)
- [x] `prop-types` adicionado (peer dep do recharts via react-transition-group) — build fix
- [x] **[MAJOR]** `src/app/dashboard/page.tsx`: Suspense fallback é `<div>Carregando...</div>` — substituir pelo mesmo Skeleton grid da `loading.tsx`
- [x] **[MINOR]** `src/app/dashboard/page.tsx`: transformar em Server Component; mover lógica de hooks para subcomponente Client; aproveita streaming SSR do Next.js 14
- [x] Integrar `NEXT_PUBLIC_API_URL` no `.env` (já em `.env` local: `http://localhost:8000`)
- [ ] Testar dashboard mobile-friendly (breakpoints 375px, 768px, 1280px)
- [ ] Deploy Railway/Render (pós-infra pronta)

---

### PW-44: MapaUF + SetorRanking + Export CSV ✅ Done (build clean)
- [x] `src/components/MapaUF.tsx` — dynamic import wrapper (evita SSR crash do Leaflet)
- [x] `src/components/MapaUFInner.tsx` — MapContainer OpenStreetMap base, legenda
- [x] `src/components/SetorRanking.tsx` — TanStack Table, ordenação, busca global, export CSV
- [x] Export CSV funcional via `SetorRanking`
- [x] **[MAJOR]** `MapaUFInner.tsx`: coroplético real implementado — GeoJSON IBGE via API pública + colorização verde/vermelho por saldo; endpoint `/v1/caged/map` adicionado na API
- [ ] Comparador de setores (selecionar até 3 para análise paralela) — diferido para pós-MVP
- [ ] Lighthouse performance > 80 (medir pós-deploy)

---

## Fixes do Code Review — Prioritários (pré-produção)

### BLOQUEADORES (não deployar sem corrigir) ✅ TODOS RESOLVIDOS
- [x] **init.sql** — remover `PARTITION BY RANGE` (MAJOR-5 → docker-compose falha)
- [x] **db.py** — warmup Redis no lifespan startup (CRITICAL-2)
- [x] **caged.py** — SQL estático sem f-string no WHERE (CRITICAL-3)
- [x] **caged.py** — mapping UF sigla→IBGE code (MINOR-10 / bug funcional)
- [x] **transform.py** — validar csv_path antes de interpolar em SQL (CRITICAL-1)

### ANTES DO PRIMEIRO USUÁRIO
- [x] **validate.py** — capturar `SchemaError` singular (MAJOR-8)
- [x] **cache.py** — KEYS → SCAN cursor (MAJOR-2)
- [x] **main.py** — CORS origins para Settings (MAJOR-4)
- [x] **docker-compose.yml** — healthcheck no serviço api (MAJOR-3)
- [x] **dashboard/page.tsx** — Suspense fallback skeleton (MAJOR-6)
- [x] **MapaUFInner.tsx** — coroplético real implementado (MAJOR-7)

---

## Fase 2 — Compliance + Monetização | Meta: 2026-06-07
> Não iniciar até Fase 1 completa + todos os BLOQUEADORES resolvidos

### PW-45 (Epic): Compliance Score + Stripe
- [ ] **PW-45a** Score de compliance por CNPJ (cruzamento CNJ + MTE + RAIS)
  - [ ] ETL do CNJ (dados de processos trabalhistas)
  - [ ] Algoritmo de scoring (pesos por fonte de risco)
  - [ ] `GET /v1/compliance/{cnpj}` — retorna score + detalhamento
  - [ ] Cache Redis 24h por CNPJ
- [ ] **PW-45b** Integração Stripe para plano Pro
  - [ ] Webhook Stripe (checkout.session.completed, invoice.payment_failed)
  - [ ] Tabela `users` — campo `plano` atualizado via webhook
  - [ ] Middleware de autenticação por API key (SHA-256 hash)
  - [ ] Rate limiting por plano (Free: 100 req/dia, Pro: ilimitado)
- [ ] **PW-48** Turnover Benchmarking Beta (CAGED only, sem RAIS)
  - [ ] `GET /v1/turnover/benchmark?cnae2=&uf=&porte=` — percentis p25/p50/p75/p90
  - [ ] Cálculo via dbt model `int_turnover_caged.sql`
  - [ ] UI: card de benchmark no dashboard (Fase 2 feature gate)

---

## Fase 3 — Relatórios + Alertas | Meta: 2026-07-19
> Não iniciar até Fase 2 completa

### PW-46 (Epic): Relatórios PDF + Alertas Email
- [ ] Geração de relatórios PDF (headless Chrome ou WeasyPrint)
- [ ] Alertas por email (variação de saldo > threshold configurável)
- [ ] Painel de alertas no dashboard
- [ ] Agendamento de relatórios recorrentes

---

## Fase 4 — Crescimento | Meta: 2026-10-01
> Priorizar com base em feedback dos clientes pagantes da Fase 2

### PW-47 (Epic): RAIS + Turnover Completo + API Pública
- [ ] **PW-49** Turnover completo com RAIS (denominador real de vínculos)
  - [ ] `etl/flows/rais_flow.py` — download anual RAIS (~5GB, publicado em maio/ano seguinte)
  - [ ] `dbt/models/marts/mart_turnover_setorial.sql` — percentis com RAIS
  - [ ] `GET /v1/turnover/{cnpj}` — posicionamento do CNPJ vs. setor
  - [ ] UI: badge "Dados de YYYY" com aviso de defasagem de 5 meses
- [ ] API Pública com documentação (OpenAPI + portal de developers)
- [ ] SDK Python e Node (geração automática via openapi-generator)
- [ ] Painel de uso de API (req/dia, latência, top endpoints)

---

## Backlog / Dívida Técnica

- [ ] Adicionar `pyarrow` ao `pyproject.toml` do ETL (atualmente ausente — DuckDB usado como workaround nos testes)
- [ ] Configurar `mypy --strict` no CI e corrigir anotações faltantes (ex: parâmetro `redis` no router)
- [ ] Extrair SQL de aggregação do `transform.py` para constante compartilhada com os testes
- [ ] Adicionar testes de integração ponta-a-ponta (API + banco real via testcontainers)
- [ ] Documentar operação do ETL no README (como rodar backfill manual)
- [ ] Revisar `ADMISSAO_THRESHOLD = 30` contra codebook atualizado do MTE
