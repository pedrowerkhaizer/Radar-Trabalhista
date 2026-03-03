# Design: Dashboard Improvements + 4 Analytical Modules

**Date:** 2026-03-03
**Status:** Approved
**Scope:** Fase 1 fixes + Fase 2 analytical expansion

---

## Context

The current dashboard (`/dashboard`) has 5 known issues and lacks depth for the target personas (HR managers, compliance officers, analysts). This design covers:

1. **Performance** — filter changes cause redundant, uncoordinated API refetches
2. **KPI aggregation** — big numbers show only the last month, not the full selected period
3. **Chart + map bugs** — series ignores custom period; map has UF code type mismatch
4. **Ranking → Monthly table** — ranking by saldo replaced with chronological evolution table
5. **4 new analytical modules** — Demográfico, Rotatividade, Ocupações, Empresa — each a separate page under `/dashboard/*`, backed by dedicated ETL tables and API endpoints

---

## Area 1 — Performance

### Problem
Every filter change fires 3 simultaneous React Query refetches (summary + series + map). A user who changes UF then CNAE then period triggers 9 fetches for what should be 1 round of data.

### Solution: Committed Filters + Debounce + Stale Time

**Zustand store** gains a second state object: `committedFilters`. The `FilterBar` writes to a local `pendingFilters` state. After 400 ms of inactivity (debounce), `pendingFilters` is committed to `committedFilters` in the store.

All three hooks (`useCagedSummary`, `useCagedSeries`, `useCagedMap`) and future module hooks derive their React Query keys from `committedFilters`, not the live `filters`. This guarantees:
- All 3 fetches share the same filter snapshot
- Zero fetches until debounce resolves
- Switching UF + CNAE + period = 1 fetch cycle, not 9

**staleTime** increases from 5 min → 30 min. CAGED data is published monthly; there is no reason to refetch within a session.

**Files changed:**
- `apps/web/src/store/filters.ts` — add `committedFilters`, `commitFilters()`, `setPendingFilter()`
- `apps/web/src/hooks/useCaged.ts` — switch query keys to `committedFilters`
- `apps/web/src/components/FilterBar.tsx` — debounce commits via `useEffect`

---

## Area 2 — KPI Period Aggregation

### Problem
`DashboardContent.tsx` uses `summaryQuery.data?.data?.[0]` — the first (latest) item. KPIs show a single month regardless of the selected period.

### Solution: Client-side Reduction

The `/summary` endpoint already returns all months for the selected period (up to 60). The fix is to reduce the array:

```ts
const totals = useMemo(() => {
  const rows = summaryQuery.data?.data ?? []
  return {
    admissoes:     rows.reduce((s, r) => s + r.admissoes, 0),
    desligamentos: rows.reduce((s, r) => s + r.desligamentos, 0),
    saldo:         rows.reduce((s, r) => s + r.saldo, 0),
    salario_medio: rows.length ? rows.reduce((s, r) => s + (r.salario_medio ?? 0), 0) / rows.length : 0,
  }
}, [summaryQuery.data])
```

Delta % for saldo compares the first month vs. the last month in the period (not vs. a fixed baseline).

**Files changed:**
- `apps/web/src/app/dashboard/DashboardContent.tsx`

---

## Area 3 — Chart and Map Fixes

### Chart: Series ignores custom period

The `/series` endpoint accepts `meses` (rolling window from today). When `periodo_inicio`/`periodo_fim` are set, the hook should switch to using the `/summary` data (which respects exact date ranges) as the chart's data source, instead of calling `/series` separately.

**Logic:**
- If `committedFilters.periodo_inicio` is set → chart data = `summaryQuery.data.data` (sorted ascending)
- Otherwise → chart data = `seriesQuery.data.series` (rolling `meses` window)

This eliminates a redundant API call when custom dates are active.

**Files changed:**
- `apps/web/src/app/dashboard/DashboardContent.tsx` — conditional chart data source
- `apps/web/src/hooks/useCaged.ts` — `useCagedSeries` skips fetch when period filters are active (`enabled: !committedFilters.periodo_inicio`)

### Map: UF code type mismatch

The `/map` endpoint returns `uf` as string IBGE 2-digit code (`"35"`). `MapaUFInner` looks up `saldoByUF[feature?.properties?.codarea]` where `codarea` from the IBGE GeoJSON is also a string. The bug is that the API response may serialize `uf` as an integer in some rows, causing the string lookup to miss.

**Fix:** Normalize `uf` to string in `MapaUFInner` when building `saldoByUF`:
```ts
for (const item of data) {
  saldoByUF[String(item.uf)] = item.saldo
}
```

**Files changed:**
- `apps/web/src/components/MapaUFInner.tsx`

---

## Area 4 — Monthly Evolution Table

### Problem
`SetorRanking` shows CAGED summary rows sorted by saldo descending — it reads as a "top months" leaderboard, which is confusing. The right side of the dashboard should be a clean chronological evolution of the data.

### Solution: Replace with `TabelaEvolucaoMensal`

New component replaces `SetorRanking`. Columns:
| Mês | Admissões | Demissões | Saldo | Salário Médio |
|-----|-----------|-----------|-------|---------------|

- Sorted by competência **ascending** (oldest → newest)
- Saldo cell colored green/red
- CSV export retained
- Source: `summaryQuery.data.data` (already available, no new API call)

**Files changed:**
- `apps/web/src/components/TabelaEvolucaoMensal.tsx` (new)
- `apps/web/src/app/dashboard/DashboardContent.tsx` — swap component

---

## Area 5 — Four New Analytical Modules

### 5a — Data Architecture (ETL)

Three new PostgreSQL tables loaded via a new ETL script (`etl/bq_backfill_dims.py`):

#### `fato_caged_demog`
Grain: `(competencia, cnae2, uf, sexo, faixa_etaria, grau_instrucao, raca_cor)`

| Column | Type | Source (BigQuery) |
|--------|------|-------------------|
| competencia | DATE | ano + mes → DATE |
| cnae2 | CHAR(2) | cnae_2 |
| uf | CHAR(2) | sigla_uf → IBGE code |
| sexo | CHAR(1) | sexo (1=M, 3=F, 9=Ignorado) |
| faixa_etaria | VARCHAR(10) | idade → bucket (18-24, 25-34, 35-44, 45-54, 55+) |
| grau_instrucao | SMALLINT | grau_instrucao (1-9) |
| raca_cor | SMALLINT | raca_cor (1-6) |
| admissoes | INTEGER | COUNT WHERE tipo_movimentacao IN admissão |
| desligamentos | INTEGER | COUNT WHERE tipo_movimentacao IN desligamento |
| saldo | INTEGER | admissoes - desligamentos |
| salario_medio | NUMERIC(10,2) | AVG(salario_mensal) |

PK: `(competencia, cnae2, uf, sexo, faixa_etaria, grau_instrucao, raca_cor)`
Estimated rows 2024: ~2M (much smaller than fato_caged because UF-level, not municipio)

#### `fato_caged_rotat`
Grain: `(competencia, cnae2, uf, causa_desligamento, tipo_vinculo, faixa_tempo_emprego)`

| Column | Type | Notes |
|--------|------|-------|
| causa_desligamento | SMALLINT | 11=sem justa causa, 21=pedido, etc. |
| tipo_vinculo | SMALLINT | 10=CLT, 40=Aprendiz, etc. |
| faixa_tempo_emprego | VARCHAR(10) | 0-3m, 3-6m, 6-12m, 1-2a, 2-5a, 5a+ |
| desligamentos | INTEGER | count only desligamentos |
| salario_medio | NUMERIC(10,2) | |

PK: `(competencia, cnae2, uf, causa_desligamento, tipo_vinculo, faixa_tempo_emprego)`

#### `fato_caged_empresa`
Grain: `(competencia, cnae2, uf, porte_empresa, tipo_vinculo)`

| Column | Type | Notes |
|--------|------|-------|
| porte_empresa | SMALLINT | 1=1-10, 2=11-50, 3=51-200, 4=201-500, 5=501-1000, 6=1001+ |
| tipo_vinculo | SMALLINT | |
| admissoes | INTEGER | |
| desligamentos | INTEGER | |
| saldo | INTEGER | |
| salario_medio | NUMERIC(10,2) | |

PK: `(competencia, cnae2, uf, porte_empresa, tipo_vinculo)`

#### Ocupações module
Uses existing `fato_caged` (has `cbo6`) + `ref_cbo` (has `descricao`, `grupo`). No new ETL table needed — just new API endpoint that joins these two.

#### ETL script
`etl/bq_backfill_dims.py` — mirrors structure of existing `bq_backfill.py`:
- Loops year/month for 2023-2024 backfill
- Three BigQuery queries (one per table)
- psycopg3 COPY for bulk insert
- Idempotent: TRUNCATE + reload per month

### 5b — API Endpoints

New router: `apps/api/routers/analytics.py`
Prefix: `/v1/analytics`

| Endpoint | Module | Description |
|----------|--------|-------------|
| `GET /demografico/genero` | Demográfico | Admissões/demissões by sexo over time |
| `GET /demografico/escolaridade` | Demográfico | Distribution by grau_instrucao |
| `GET /demografico/faixa-etaria` | Demográfico | Distribution by faixa_etaria |
| `GET /rotatividade/causas` | Rotatividade | Desligamentos by causa_desligamento |
| `GET /rotatividade/tempo-emprego` | Rotatividade | Distribution by faixa_tempo_emprego |
| `GET /rotatividade/tipo-vinculo` | Rotatividade | Mix by tipo_vinculo |
| `GET /ocupacoes/ranking` | Ocupações | Top CBO families by admissões/saldo |
| `GET /ocupacoes/salario` | Ocupações | Salary by CBO group |
| `GET /empresa/porte` | Empresa | Admissões/demissões by porte_empresa |
| `GET /empresa/tipo-vinculo` | Empresa | Contract type mix |

All endpoints: same pattern as `caged.py` (Redis cache 1h, dynamic WHERE, asyncpg-safe params).

New router: `apps/api/routers/cbo.py`
`GET /v1/cbo/occupations` — list CBO groups with admissões/saldo, supports cnae2 filter

### 5c — Frontend Pages

New pages under Next.js App Router:

```
apps/web/src/app/dashboard/
├── demografico/
│   ├── page.tsx          ← "Perfil Demográfico"
│   └── DemograficoContent.tsx
├── rotatividade/
│   ├── page.tsx          ← "Rotatividade"
│   └── RotatividadeContent.tsx
├── ocupacoes/
│   ├── page.tsx          ← "Ocupações (CBO)"
│   └── OcupacoesContent.tsx
└── empresa/
    ├── page.tsx          ← "Perspectiva Empresa"
    └── EmpresaContent.tsx
```

**Shared layout per module:**
1. `FilterBar` (shared, CNAE + UF + período — same as main dashboard)
2. KPI strip (2-3 metrics specific to the module)
3. Primary chart (bar/line specific to module)
4. Secondary chart or table

**Module specifics:**

| Module | KPIs | Primary Chart | Secondary |
|--------|------|---------------|-----------|
| Demográfico | % feminino, saldo F vs M | Barras agrupadas M/F por mês | Distribuição por escolaridade (donut) |
| Rotatividade | Taxa desligamento sem causa, média tempo emprego | Barras por causa desligamento | Tabela top causas por setor |
| Ocupações | Top CBO por admissões, maior saldo por grupo | Ranking horizontal (bar) por CBO família | Tabela CBO com salário médio |
| Empresa | % admissões em micro (<10), dominante por porte | Barras empilhadas por porte | Salário médio por porte (linha) |

**Sidebar update:**
```
Dashboard Principal
Demográfico          ← new
Rotatividade         ← new
Ocupações            ← new
Perspectiva Empresa  ← new
```

**New hooks:**
- `apps/web/src/hooks/useAnalytics.ts` — hooks for all 4 modules, same pattern as `useCaged.ts`
- `apps/web/src/lib/api-client.ts` — add fetch functions for each endpoint

---

## Implementation Order

Suggested sequence to maximize early wins:

1. **Performance fix** (Area 1) — immediate UX improvement, enables faster testing of everything else
2. **KPI aggregation + chart/map fixes + monthly table** (Areas 2-4) — fixes existing dashboard correctness
3. **ETL re-run** — `bq_backfill_dims.py` for 3 new tables (can run in background)
4. **API endpoints** — `analytics.py` router + `cbo.py` router
5. **Module UIs** — 4 new pages (can be parallelized per module)

---

## Linear Issues to Create

| Issue | Area | Phase |
|-------|------|-------|
| PW-?? Performance: committed filters + debounce + stale time | Area 1 | Fase 1 |
| PW-?? Fix KPI period aggregation | Area 2 | Fase 1 |
| PW-?? Fix chart period sync + map UF type | Area 3 | Fase 1 |
| PW-?? Replace SetorRanking with TabelaEvolucaoMensal | Area 4 | Fase 1 |
| PW-?? ETL: bq_backfill_dims.py (demog + rotat + empresa) | Area 5 | Fase 2 |
| PW-?? API: /v1/analytics router (10 endpoints) | Area 5 | Fase 2 |
| PW-?? API: /v1/cbo/occupations | Area 5 | Fase 2 |
| PW-?? UI: Módulo Demográfico | Area 5 | Fase 2 |
| PW-?? UI: Módulo Rotatividade | Area 5 | Fase 2 |
| PW-?? UI: Módulo Ocupações | Area 5 | Fase 2 |
| PW-?? UI: Módulo Empresa | Area 5 | Fase 2 |

---

## Out of Scope

- Gender prediction or enrichment beyond CAGED `sexo` field
- RAIS integration (Fase 4, PW-49)
- Real-time data (CAGED is monthly)
- Individual CNPJ lookup (Fase 4)
- Race/ethnicity analysis (`raca_cor`) — included in ETL grain but no dedicated UI in this iteration
