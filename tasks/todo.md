# Radar Trabalhista — Task Tracker

## Fase 1 — Fundação (Semanas 1-6) | Meta: 2026-04-12

### PW-40: Setup infra: Docker Compose + PostgreSQL + TimescaleDB + GitHub CI
- [x] Estrutura de pastas do monorepo criada
- [x] `infra/docker-compose.yml` com todos os serviços
- [x] `infra/init.sql` com schema completo
- [x] `.github/workflows/ci.yml`
- [x] `Makefile` com targets principais
- [x] `.gitignore` e `.env.example`
- [ ] Dockerfile para apps/api
- [ ] Dockerfile para apps/web
- [ ] Testar `docker-compose up` localmente

### PW-41: Pipeline ETL CAGED
- [x] Estrutura de flows/tasks criada (stubs)
- [ ] Implementar `tasks/download.py`
- [ ] Implementar `tasks/validate.py` (schema Pandera)
- [ ] Implementar `tasks/transform.py` (DuckDB aggregation)
- [ ] Implementar `tasks/load.py` (psycopg3 COPY)
- [ ] dbt models: stg_caged + mart_mercado_trabalho
- [ ] Carregar 12 meses históricos
- [ ] Configurar schedule Prefect

### PW-42: API FastAPI endpoints CAGED
- [x] Estrutura apps/api criada (stubs)
- [ ] Implementar queries reais no PostgreSQL
- [ ] Implementar Redis cache
- [ ] Testes pytest (cobertura > 70%)
- [ ] Dockerfile

### PW-43: Frontend Next.js Landing + Dashboard
- [ ] Setup Next.js 14 App Router + TypeScript
- [ ] FilterBar, KPICard, CAGEDChart
- [ ] TanStack Query + Zustand
- [ ] Deploy Railway/Render

### PW-44: MapaUF + SetorRanking + exportação CSV
- [ ] MapaUF (react-leaflet + GeoJSON)
- [ ] SetorRanking (TanStack Table)
- [ ] Exportação CSV
- [ ] Comparador de setores

---

## Fase 2 — Compliance + Monetização (Semanas 7-14) | Meta: 2026-06-07
> Não iniciar até Fase 1 completa

- [ ] PW-45 (Epic) — ver detalhes no Linear

## Fase 3 — Relatórios + Alertas (Semanas 15-20) | Meta: 2026-07-19
> Não iniciar até Fase 2 completa

- [ ] PW-46 (Epic) — ver detalhes no Linear

## Fase 4 — Crescimento (Pós-20) | Meta: 2026-10-01
> Priorizar com base em feedback dos clientes pagantes da Fase 2

- [ ] PW-47 (Epic) — ver detalhes no Linear
