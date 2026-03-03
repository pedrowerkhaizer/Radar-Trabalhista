# Dashboard Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 dashboard correctness bugs, improve filter performance, and add 4 new analytical module pages (Demográfico, Rotatividade, Ocupações, Empresa).

**Architecture:** Zustand committed-filters pattern eliminates redundant refetches; client-side reduce fixes KPI aggregation; 3 new PostgreSQL fact tables feed a `/v1/analytics` router; 4 new Next.js pages follow the existing DashboardContent pattern.

**Tech Stack:** Next.js 14 App Router, Zustand, TanStack Query, Recharts, FastAPI, asyncpg, Redis, Python psycopg3, BigQuery.

---

## Phase 1 — Frontend Fixes (no new API calls needed)

### Task 1: Performance — Committed Filters + Debounce

**Files:**
- Modify: `apps/web/src/store/filters.ts`
- Modify: `apps/web/src/hooks/useCaged.ts`
- Modify: `apps/web/src/components/FilterBar.tsx`

**Step 1: Update the Zustand store**

Replace the entire content of `apps/web/src/store/filters.ts`:

```ts
import { create } from "zustand"
import type { FilterState } from "@/lib/types"

interface FilterStore {
  filters: FilterState
  committedFilters: FilterState
  setFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void
  commitFilters: () => void
  resetFilters: () => void
}

const DEFAULT_FILTERS: FilterState = { meses: 12 }

export const useFiltersStore = create<FilterStore>((set, get) => ({
  filters: DEFAULT_FILTERS,
  committedFilters: DEFAULT_FILTERS,
  setFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),
  commitFilters: () => set((state) => ({ committedFilters: state.filters })),
  resetFilters: () => set({ filters: DEFAULT_FILTERS, committedFilters: DEFAULT_FILTERS }),
}))
```

**Step 2: Update hooks to use committedFilters + 30min staleTime**

Replace the entire content of `apps/web/src/hooks/useCaged.ts`:

```ts
"use client"
import { useQuery } from "@tanstack/react-query"
import { fetchCAGEDSummary, fetchCAGEDSeries, fetchCAGEDMap } from "@/lib/api-client"
import type { FilterState } from "@/lib/types"

const STALE_TIME = 30 * 60 * 1000 // 30 minutes — CAGED is monthly data

export function useCagedSummary(filters: Partial<FilterState>) {
  return useQuery({
    queryKey: ["caged", "summary", filters],
    queryFn: () => fetchCAGEDSummary(filters),
    staleTime: STALE_TIME,
    retry: 2,
  })
}

export function useCagedSeries(filters: Partial<FilterState>, meses = 12) {
  return useQuery({
    queryKey: ["caged", "series", filters, meses],
    queryFn: () => fetchCAGEDSeries(filters, meses),
    staleTime: STALE_TIME,
    retry: 2,
    // When a custom date range is active, /summary already covers this data
    enabled: !filters.periodo_inicio,
  })
}

export function useCagedMap(filters: Partial<FilterState>) {
  return useQuery({
    queryKey: ["caged", "map", filters],
    queryFn: () => fetchCAGEDMap(filters),
    staleTime: STALE_TIME,
    retry: 2,
  })
}
```

**Step 3: Add debounce to FilterBar**

Replace the `useEffect` block in `apps/web/src/components/FilterBar.tsx` (lines 12-31) with a two-effect pattern — one for URL sync (existing), one for debounced commit:

```tsx
"use client"
import { useFiltersStore } from "@/store/filters"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { CNAE_OPTIONS, UF_OPTIONS } from "@/lib/types"
import { Filter, X } from "lucide-react"

export function FilterBar() {
  const { filters, setFilter, resetFilters, commitFilters } = useFiltersStore()
  const router = useRouter()

  // Sync filters to URL params
  useEffect(() => {
    const params = new URLSearchParams()
    if (filters.cnae2) params.set("cnae2", filters.cnae2)
    else params.delete("cnae2")
    if (filters.uf) params.set("uf", filters.uf)
    else params.delete("uf")
    if (filters.meses !== 12) params.set("meses", String(filters.meses))
    else params.delete("meses")
    router.replace(`?${params.toString()}`, { scroll: false })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, router])

  // Debounce: commit to query keys after 400ms of inactivity
  useEffect(() => {
    const timer = setTimeout(() => {
      commitFilters()
    }, 400)
    return () => clearTimeout(timer)
  }, [filters, commitFilters])

  const hasActiveFilters = filters.cnae2 || filters.uf || filters.meses !== 12

  function clearFilters() {
    resetFilters()
  }

  return (
    // ... rest of JSX unchanged (selects call setFilter, not commitFilters directly)
  )
}
```

**Step 4: Update DashboardContent to use committedFilters**

In `apps/web/src/app/dashboard/DashboardContent.tsx`, change line 11:
```ts
// Before:
const { filters } = useFiltersStore()
// After:
const { committedFilters: filters } = useFiltersStore()
```

**Step 5: Verify the app builds**

```bash
cd apps/web && npm run build 2>&1 | tail -20
```
Expected: `✓ Compiled successfully`

**Step 6: Commit**

```bash
git add apps/web/src/store/filters.ts apps/web/src/hooks/useCaged.ts apps/web/src/components/FilterBar.tsx apps/web/src/app/dashboard/DashboardContent.tsx
git commit -m "PW-??: perf: committed filters + 400ms debounce + 30min staleTime"
```

---

### Task 2: KPI Period Aggregation

**Files:**
- Modify: `apps/web/src/app/dashboard/DashboardContent.tsx`

**Step 1: Replace `latest` with a `useMemo` reduction**

Add this import at the top of `DashboardContent.tsx`:
```ts
import { useMemo } from "react"
```

Replace line 15 (`const latest = summaryQuery.data?.data?.[0]`) with:

```ts
const totals = useMemo(() => {
  const rows = summaryQuery.data?.data ?? []
  if (rows.length === 0) return null
  return {
    admissoes:     rows.reduce((s, r) => s + r.admissoes, 0),
    desligamentos: rows.reduce((s, r) => s + r.desligamentos, 0),
    saldo:         rows.reduce((s, r) => s + r.saldo, 0),
    // delta: compare first month vs last month (summary returns DESC, so [0]=newest, [last]=oldest)
    saldoDelta: rows.length > 1
      ? ((rows[0].saldo - rows[rows.length - 1].saldo) / Math.max(Math.abs(rows[rows.length - 1].saldo), 1)) * 100
      : 0,
    salario_medio: rows.reduce((s, r) => s + (r.salario_medio ?? 0), 0) / rows.length,
  }
}, [summaryQuery.data])
```

Replace KPI cards to use `totals` instead of `latest`:
```tsx
<KPICard
  title="Saldo Líquido"
  value={totals?.saldo ?? 0}
  delta={totals?.saldoDelta}
  trend={totals && totals.saldo >= 0 ? "up" : "down"}
  sparklineData={sparkline}
  isLoading={summaryQuery.isLoading}
  description="Admissões − Demissões no período"
/>
<KPICard title="Admissões" value={totals?.admissoes ?? 0} trend="up" isLoading={summaryQuery.isLoading} description="Total no período" />
<KPICard title="Demissões" value={totals?.desligamentos ?? 0} trend="down" isLoading={summaryQuery.isLoading} description="Total no período" />
<KPICard title="Salário Médio" value={totals?.salario_medio ?? 0} prefix="R$ " trend="neutral" isLoading={summaryQuery.isLoading} description="Média das admissões" />
```

**Step 2: Verify build**

```bash
cd apps/web && npm run build 2>&1 | tail -10
```
Expected: `✓ Compiled successfully`

**Step 3: Commit**

```bash
git add apps/web/src/app/dashboard/DashboardContent.tsx
git commit -m "PW-??: fix: KPI cards now aggregate full selected period instead of last month only"
```

---

### Task 3: Chart Period Sync + Map UF Type Fix

**Files:**
- Modify: `apps/web/src/app/dashboard/DashboardContent.tsx`
- Modify: `apps/web/src/components/MapaUFInner.tsx`

**Step 1: Fix map UF type mismatch in MapaUFInner.tsx**

Lines 44-49 in `MapaUFInner.tsx`, change:
```ts
// Before:
for (const item of data) {
  saldoByUF[item.uf] = item.saldo
  if (Math.abs(item.saldo) > maxAbs) maxAbs = Math.abs(item.saldo)
}
// After (normalize to string):
for (const item of data) {
  saldoByUF[String(item.uf)] = item.saldo
  if (Math.abs(item.saldo) > maxAbs) maxAbs = Math.abs(item.saldo)
}
```

**Step 2: Fix chart to use summary data when custom period is active**

In `DashboardContent.tsx`, replace the chart data line:
```ts
// Before (line 16):
const sparkline = seriesQuery.data?.series?.map((s) => s.saldo) ?? []

// After:
const hasPeriodFilter = !!filters.periodo_inicio
// When period filter is active: use summary data sorted ASC; otherwise use rolling series
const chartData = hasPeriodFilter
  ? [...(summaryQuery.data?.data ?? [])].sort((a, b) => a.competencia.localeCompare(b.competencia))
  : (seriesQuery.data?.series ?? [])
const sparkline = chartData.map((s) => s.saldo)
```

Replace the `<CAGEDChart>` usage:
```tsx
// Before:
<CAGEDChart data={seriesQuery.data?.series ?? []} isLoading={seriesQuery.isLoading} />
// After:
<CAGEDChart data={chartData} isLoading={hasPeriodFilter ? summaryQuery.isLoading : seriesQuery.isLoading} />
```

**Step 3: Verify build**

```bash
cd apps/web && npm run build 2>&1 | tail -10
```

**Step 4: Commit**

```bash
git add apps/web/src/app/dashboard/DashboardContent.tsx apps/web/src/components/MapaUFInner.tsx
git commit -m "PW-??: fix: chart uses summary data for custom periods; map normalizes UF to string"
```

---

### Task 4: TabelaEvolucaoMensal — Replace SetorRanking

**Files:**
- Create: `apps/web/src/components/TabelaEvolucaoMensal.tsx`
- Modify: `apps/web/src/app/dashboard/DashboardContent.tsx`

**Step 1: Create the component**

```tsx
// apps/web/src/components/TabelaEvolucaoMensal.tsx
"use client"
import type { CAGEDSummaryItem } from "@/lib/types"
import { cn } from "@/lib/utils"

interface Props {
  data: CAGEDSummaryItem[]
  isLoading: boolean
}

function formatNum(n: number) {
  return new Intl.NumberFormat("pt-BR").format(n)
}

function formatCurrency(n: number | null) {
  if (n == null) return "—"
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(n)
}

export function TabelaEvolucaoMensal({ data, isLoading }: Props) {
  if (isLoading) {
    return <div className="h-48 animate-pulse rounded-lg bg-slate-100" />
  }

  // Sort ascending: oldest → newest
  const rows = [...data].sort((a, b) => a.competencia.localeCompare(b.competencia))

  if (rows.length === 0) {
    return <p className="text-sm text-slate-400 text-center py-8">Sem dados para o período selecionado.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="pb-2 text-left text-xs font-semibold text-slate-500">Mês</th>
            <th className="pb-2 text-right text-xs font-semibold text-slate-500">Admissões</th>
            <th className="pb-2 text-right text-xs font-semibold text-slate-500">Demissões</th>
            <th className="pb-2 text-right text-xs font-semibold text-slate-500">Saldo</th>
            <th className="pb-2 text-right text-xs font-semibold text-slate-500">Sal. Médio</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.competencia} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
              <td className="py-1.5 font-medium text-slate-700">{row.competencia}</td>
              <td className="py-1.5 text-right text-slate-600">{formatNum(row.admissoes)}</td>
              <td className="py-1.5 text-right text-slate-600">{formatNum(row.desligamentos)}</td>
              <td className={cn(
                "py-1.5 text-right font-semibold",
                row.saldo >= 0 ? "text-emerald-600" : "text-red-600"
              )}>
                {row.saldo >= 0 ? "+" : ""}{formatNum(row.saldo)}
              </td>
              <td className="py-1.5 text-right text-slate-500">{formatCurrency(row.salario_medio)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

**Step 2: Swap component in DashboardContent.tsx**

Replace:
```tsx
import { SetorRanking } from "@/components/SetorRanking"
// ...
<h2 className="text-sm font-semibold text-slate-900 mb-4">Ranking por Competência</h2>
<SetorRanking data={summaryQuery.data?.data ?? []} isLoading={summaryQuery.isLoading} />
```
With:
```tsx
import { TabelaEvolucaoMensal } from "@/components/TabelaEvolucaoMensal"
// ...
<h2 className="text-sm font-semibold text-slate-900 mb-4">Evolução Mensal</h2>
<TabelaEvolucaoMensal data={summaryQuery.data?.data ?? []} isLoading={summaryQuery.isLoading} />
```

**Step 3: Verify build**

```bash
cd apps/web && npm run build 2>&1 | tail -10
```

**Step 4: Commit**

```bash
git add apps/web/src/components/TabelaEvolucaoMensal.tsx apps/web/src/app/dashboard/DashboardContent.tsx
git commit -m "PW-??: feat: replace SetorRanking with TabelaEvolucaoMensal sorted chronologically"
```

---

## Phase 2 — DB Migrations (3 new fact tables)

### Task 5: Create ETL Tables via SQL Migration

**Files:**
- Create: `apps/api/migrations/001_analytics_tables.sql`

**Step 1: Write the migration**

```sql
-- apps/api/migrations/001_analytics_tables.sql
-- Analytics dimension tables for Demográfico, Rotatividade, Empresa modules.
-- Run via: psql $DATABASE_URL -f apps/api/migrations/001_analytics_tables.sql

-- ── Tabela demográfica ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fato_caged_demog (
    competencia      DATE         NOT NULL,
    cnae2            CHAR(2)      NOT NULL,
    uf               CHAR(2)      NOT NULL,  -- código IBGE 2 dígitos
    sexo             CHAR(1)      NOT NULL,  -- '1'=M, '3'=F, '9'=Ignorado
    faixa_etaria     VARCHAR(10)  NOT NULL,  -- '18-24','25-34','35-44','45-54','55+'
    grau_instrucao   SMALLINT     NOT NULL,  -- 1-9 (MTE codebook)
    admissoes        INTEGER      NOT NULL DEFAULT 0,
    desligamentos    INTEGER      NOT NULL DEFAULT 0,
    saldo            INTEGER      NOT NULL DEFAULT 0,
    salario_medio    NUMERIC(10,2),
    PRIMARY KEY (competencia, cnae2, uf, sexo, faixa_etaria, grau_instrucao)
);

-- ── Tabela rotatividade ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fato_caged_rotat (
    competencia          DATE         NOT NULL,
    cnae2                CHAR(2)      NOT NULL,
    uf                   CHAR(2)      NOT NULL,
    causa_desligamento   SMALLINT     NOT NULL,  -- 11=sem justa causa, 21=pedido, etc.
    tipo_vinculo         SMALLINT     NOT NULL,  -- 10=CLT, 40=Aprendiz, etc.
    faixa_tempo_emprego  VARCHAR(10)  NOT NULL,  -- '0-3m','3-6m','6-12m','1-2a','2-5a','5a+'
    desligamentos        INTEGER      NOT NULL DEFAULT 0,
    salario_medio        NUMERIC(10,2),
    PRIMARY KEY (competencia, cnae2, uf, causa_desligamento, tipo_vinculo, faixa_tempo_emprego)
);

-- ── Tabela empresa ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fato_caged_empresa (
    competencia    DATE       NOT NULL,
    cnae2          CHAR(2)    NOT NULL,
    uf             CHAR(2)    NOT NULL,
    porte_empresa  SMALLINT   NOT NULL,  -- 1=1-10, 2=11-50, 3=51-200, 4=201-500, 5=501-1000, 6=1001+
    tipo_vinculo   SMALLINT   NOT NULL,
    admissoes      INTEGER    NOT NULL DEFAULT 0,
    desligamentos  INTEGER    NOT NULL DEFAULT 0,
    saldo          INTEGER    NOT NULL DEFAULT 0,
    salario_medio  NUMERIC(10,2),
    PRIMARY KEY (competencia, cnae2, uf, porte_empresa, tipo_vinculo)
);

-- Indexes for common filter patterns
CREATE INDEX IF NOT EXISTS idx_demog_comp_uf   ON fato_caged_demog  (competencia, uf);
CREATE INDEX IF NOT EXISTS idx_demog_comp_cnae ON fato_caged_demog  (competencia, cnae2);
CREATE INDEX IF NOT EXISTS idx_rotat_comp_uf   ON fato_caged_rotat  (competencia, uf);
CREATE INDEX IF NOT EXISTS idx_rotat_comp_cnae ON fato_caged_rotat  (competencia, cnae2);
CREATE INDEX IF NOT EXISTS idx_emp_comp_uf     ON fato_caged_empresa(competencia, uf);
CREATE INDEX IF NOT EXISTS idx_emp_comp_cnae   ON fato_caged_empresa(competencia, cnae2);
```

**Step 2: Apply migration to dev DB**

```bash
cd /path/to/project
psql $DATABASE_URL -f apps/api/migrations/001_analytics_tables.sql
```
Expected: `CREATE TABLE` × 3, `CREATE INDEX` × 6

**Step 3: Commit**

```bash
git add apps/api/migrations/001_analytics_tables.sql
git commit -m "PW-??: db: add fato_caged_demog + fato_caged_rotat + fato_caged_empresa tables"
```

---

## Phase 3 — ETL for New Tables

### Task 6: bq_backfill_dims.py

**Files:**
- Create: `etl/bq_backfill_dims.py`

**Step 1: Write the ETL script**

```python
"""
Backfill das tabelas de dimensões analíticas do CAGED.

Popula:
  - fato_caged_demog   (perfil demográfico: sexo, faixa etária, escolaridade)
  - fato_caged_rotat   (rotatividade: causa desligamento, vínculo, tempo emprego)
  - fato_caged_empresa (perspectiva empresa: porte, tipo vínculo)

Uso:
    cd etl
    uv run python bq_backfill_dims.py 2024-01 2024-12
"""
import os, sys, time
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

from google.cloud import bigquery
import psycopg

BQ_PROJECT = os.getenv("BQ_PROJECT_ID", "")
BD_DATASET = "basedosdados.br_me_caged"

_UF_IBGE: dict[str, str] = {
    "AC":"12","AL":"27","AM":"13","AP":"16","BA":"29","CE":"23","DF":"53",
    "ES":"32","GO":"52","MA":"21","MG":"31","MS":"50","MT":"51","PA":"15",
    "PB":"25","PE":"26","PI":"22","PR":"41","RJ":"33","RN":"24","RO":"11",
    "RR":"14","RS":"43","SC":"42","SE":"28","SP":"35","TO":"17",
}

def _get_db_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    sslmode = "require" if "supabase.co" in host else "prefer"
    return (f"host={host} port={os.getenv('POSTGRES_PORT','5432')} "
            f"dbname={os.getenv('POSTGRES_DB','postgres')} "
            f"user={os.getenv('POSTGRES_USER','postgres')} "
            f"password={os.getenv('POSTGRES_PASSWORD','')} sslmode={sslmode}")

def _age_bucket(age: int | None) -> str:
    if age is None: return "desconhecido"
    if age < 18: return "<18"
    if age < 25: return "18-24"
    if age < 35: return "25-34"
    if age < 45: return "35-44"
    if age < 55: return "45-54"
    return "55+"

def _tenure_bucket(months: int | None) -> str:
    if months is None: return "desconhecido"
    if months < 3: return "0-3m"
    if months < 6: return "3-6m"
    if months < 12: return "6-12m"
    if months < 24: return "1-2a"
    if months < 60: return "2-5a"
    return "5a+"

# ── BigQuery queries ─────────────────────────────────────────────────────────

DEMOG_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                          AS competencia,
    LPAD(SUBSTR(CAST(cnae_2_subclasse AS STRING), 1, 2), 2, '0')             AS cnae2,
    ANY_VALUE(sigla_uf)                                                       AS sigla_uf,
    CAST(sexo AS STRING)                                                      AS sexo,
    CASE
        WHEN CAST(idade AS INT64) < 18  THEN '<18'
        WHEN CAST(idade AS INT64) < 25  THEN '18-24'
        WHEN CAST(idade AS INT64) < 35  THEN '25-34'
        WHEN CAST(idade AS INT64) < 45  THEN '35-44'
        WHEN CAST(idade AS INT64) < 55  THEN '45-54'
        ELSE '55+'
    END                                                                       AS faixa_etaria,
    CAST(grau_instrucao_apos_2005 AS INT64)                                   AS grau_instrucao,
    COUNTIF(saldo_movimentacao > 0)                                           AS admissoes,
    COUNTIF(saldo_movimentacao < 0)                                           AS desligamentos,
    AVG(IF(salario_mensal > 0 AND salario_mensal < 100000, salario_mensal, NULL)) AS salario_medio
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano = @ano AND mes = @mes
GROUP BY 1, 2, 4, 5, 6
"""

ROTAT_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                          AS competencia,
    LPAD(SUBSTR(CAST(cnae_2_subclasse AS STRING), 1, 2), 2, '0')             AS cnae2,
    ANY_VALUE(sigla_uf)                                                       AS sigla_uf,
    CAST(motivo_desligamento AS INT64)                                        AS causa_desligamento,
    CAST(tipo_vinculo AS INT64)                                               AS tipo_vinculo,
    CASE
        WHEN CAST(tempo_emprego AS FLOAT64) < 3   THEN '0-3m'
        WHEN CAST(tempo_emprego AS FLOAT64) < 6   THEN '3-6m'
        WHEN CAST(tempo_emprego AS FLOAT64) < 12  THEN '6-12m'
        WHEN CAST(tempo_emprego AS FLOAT64) < 24  THEN '1-2a'
        WHEN CAST(tempo_emprego AS FLOAT64) < 60  THEN '2-5a'
        ELSE '5a+'
    END                                                                       AS faixa_tempo_emprego,
    COUNTIF(saldo_movimentacao < 0)                                           AS desligamentos,
    AVG(IF(salario_mensal > 0 AND salario_mensal < 100000, salario_mensal, NULL)) AS salario_medio
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano = @ano AND mes = @mes AND saldo_movimentacao < 0
GROUP BY 1, 2, 4, 5, 6
"""

EMPRESA_QUERY = """
SELECT
    DATE(CAST(ano AS INT64), CAST(mes AS INT64), 1)                          AS competencia,
    LPAD(SUBSTR(CAST(cnae_2_subclasse AS STRING), 1, 2), 2, '0')             AS cnae2,
    ANY_VALUE(sigla_uf)                                                       AS sigla_uf,
    CAST(tamanho_estabelecimento AS INT64)                                    AS porte_empresa,
    CAST(tipo_vinculo AS INT64)                                               AS tipo_vinculo,
    COUNTIF(saldo_movimentacao > 0)                                           AS admissoes,
    COUNTIF(saldo_movimentacao < 0)                                           AS desligamentos,
    AVG(IF(salario_mensal > 0 AND salario_mensal < 100000, salario_mensal, NULL)) AS salario_medio
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano = @ano AND mes = @mes
GROUP BY 1, 2, 4, 5
"""

# ── Load helpers ─────────────────────────────────────────────────────────────

def _run_bq(client: bigquery.Client, query: str, ano: int, mes: int) -> list:
    job_config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("ano", "INT64", ano),
        bigquery.ScalarQueryParameter("mes", "INT64", mes),
    ], use_query_cache=True)
    return list(client.query(query, job_config=job_config).result())

def _load_demog(conn: psycopg.Connection, competencia_date: str, rows: list) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM fato_caged_demog WHERE competencia = %s::date", (competencia_date,))
        cols = "competencia,cnae2,uf,sexo,faixa_etaria,grau_instrucao,admissoes,desligamentos,saldo,salario_medio"
        with cur.copy(f"COPY fato_caged_demog ({cols}) FROM STDIN") as copy:
            for r in rows:
                uf = _UF_IBGE.get(str(r.sigla_uf or ""), "00")
                saldo = int(r.admissoes or 0) - int(r.desligamentos or 0)
                sal = min(float(r.salario_medio), 9999999.99) if r.salario_medio else None
                copy.write_row((competencia_date, str(r.cnae2 or "00")[:2], uf,
                                str(r.sexo or "9")[:1], str(r.faixa_etaria or "desconhecido"),
                                int(r.grau_instrucao or 0),
                                int(r.admissoes or 0), int(r.desligamentos or 0), saldo, sal))
    return len(rows)

def _load_rotat(conn: psycopg.Connection, competencia_date: str, rows: list) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM fato_caged_rotat WHERE competencia = %s::date", (competencia_date,))
        cols = "competencia,cnae2,uf,causa_desligamento,tipo_vinculo,faixa_tempo_emprego,desligamentos,salario_medio"
        with cur.copy(f"COPY fato_caged_rotat ({cols}) FROM STDIN") as copy:
            for r in rows:
                uf = _UF_IBGE.get(str(r.sigla_uf or ""), "00")
                sal = min(float(r.salario_medio), 9999999.99) if r.salario_medio else None
                copy.write_row((competencia_date, str(r.cnae2 or "00")[:2], uf,
                                int(r.causa_desligamento or 0), int(r.tipo_vinculo or 0),
                                str(r.faixa_tempo_emprego or "desconhecido"),
                                int(r.desligamentos or 0), sal))
    return len(rows)

def _load_empresa(conn: psycopg.Connection, competencia_date: str, rows: list) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM fato_caged_empresa WHERE competencia = %s::date", (competencia_date,))
        cols = "competencia,cnae2,uf,porte_empresa,tipo_vinculo,admissoes,desligamentos,saldo,salario_medio"
        with cur.copy(f"COPY fato_caged_empresa ({cols}) FROM STDIN") as copy:
            for r in rows:
                uf = _UF_IBGE.get(str(r.sigla_uf or ""), "00")
                saldo = int(r.admissoes or 0) - int(r.desligamentos or 0)
                sal = min(float(r.salario_medio), 9999999.99) if r.salario_medio else None
                copy.write_row((competencia_date, str(r.cnae2 or "00")[:2], uf,
                                int(r.porte_empresa or 0), int(r.tipo_vinculo or 0),
                                int(r.admissoes or 0), int(r.desligamentos or 0), saldo, sal))
    return len(rows)

# ── Main ─────────────────────────────────────────────────────────────────────

def run_backfill(client: bigquery.Client, competencias: list[str]) -> None:
    dsn = _get_db_dsn()
    for comp in competencias:
        ano, mes = map(int, comp.split("-"))
        competencia_date = f"{comp}-01"
        print(f"\n[bq_backfill_dims] ▶ {comp} ...")
        t0 = time.monotonic()
        try:
            demog_rows   = _run_bq(client, DEMOG_QUERY,   ano, mes)
            rotat_rows   = _run_bq(client, ROTAT_QUERY,   ano, mes)
            empresa_rows = _run_bq(client, EMPRESA_QUERY, ano, mes)
        except Exception as exc:
            print(f"[bq_backfill_dims] ✗ {comp}: BigQuery error — {exc}")
            continue
        with psycopg.connect(dsn) as conn:
            n1 = _load_demog(conn, competencia_date, demog_rows)
            n2 = _load_rotat(conn, competencia_date, rotat_rows)
            n3 = _load_empresa(conn, competencia_date, empresa_rows)
            conn.commit()
        print(f"[bq_backfill_dims] ✓ {comp}: demog={n1} rotat={n2} empresa={n3} ({time.monotonic()-t0:.1f}s)")

def main() -> None:
    if not BQ_PROJECT:
        print("Erro: BQ_PROJECT_ID não definido no .env"); sys.exit(1)
    client = bigquery.Client(project=BQ_PROJECT)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Uso: uv run python bq_backfill_dims.py ANO-MES [ANO-MES_FIM]"); sys.exit(1)
    if len(args) == 1:
        competencias = [args[0]]
    else:
        sy, sm = map(int, args[0].split("-"))
        ey, em = map(int, args[1].split("-"))
        competencias, y, m = [], sy, sm
        while (y, m) <= (ey, em):
            competencias.append(f"{y:04d}-{m:02d}")
            m += 1
            if m > 12: m, y = 1, y + 1
    print(f"[bq_backfill_dims] Competências: {competencias}")
    run_backfill(client, competencias)
    print("\n[bq_backfill_dims] Concluído!")

if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add etl/bq_backfill_dims.py
git commit -m "PW-??: etl: add bq_backfill_dims.py for demog/rotat/empresa tables"
```

> **Note:** Run the actual backfill as a separate operation after the API is deployed:
> `cd etl && uv run python bq_backfill_dims.py 2023-01 2024-12`

---

## Phase 4 — API Endpoints

### Task 7: Pydantic Schemas for Analytics

**Files:**
- Create: `apps/api/schemas/analytics.py`

**Step 1: Write the schemas**

```python
# apps/api/schemas/analytics.py
from typing import Optional
from pydantic import BaseModel, ConfigDict


class GeneroItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    competencia: str
    sexo: str
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class GeneroResponse(BaseModel):
    data: list[GeneroItem]
    total: int


class EscolaridadeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    grau_instrucao: int
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class EscolaridadeResponse(BaseModel):
    data: list[EscolaridadeItem]


class FaixaEtariaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    faixa_etaria: str
    admissoes: int
    desligamentos: int
    saldo: int


class FaixaEtariaResponse(BaseModel):
    data: list[FaixaEtariaItem]


class CausaDesligamentoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    causa_desligamento: int
    desligamentos: int
    salario_medio: Optional[float] = None


class CausaDesligamentoResponse(BaseModel):
    data: list[CausaDesligamentoItem]


class TempoEmpregoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    faixa_tempo_emprego: str
    desligamentos: int


class TempoEmpregoResponse(BaseModel):
    data: list[TempoEmpregoItem]


class TipoVinculoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tipo_vinculo: int
    admissoes: int
    desligamentos: int
    saldo: int


class TipoVinculoResponse(BaseModel):
    data: list[TipoVinculoItem]


class PorteEmpresaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    porte_empresa: int
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class PorteEmpresaResponse(BaseModel):
    data: list[PorteEmpresaItem]


class OcupacaoRankingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cbo_grupo: str  # first 2 digits of cbo6
    descricao: Optional[str] = None
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class OcupacaoRankingResponse(BaseModel):
    data: list[OcupacaoRankingItem]
    total: int
```

**Step 2: Commit**

```bash
git add apps/api/schemas/analytics.py
git commit -m "PW-??: api: add Pydantic schemas for analytics endpoints"
```

---

### Task 8: CBO Router

**Files:**
- Create: `apps/api/routers/cbo.py`
- Modify: `apps/api/main.py`

**Step 1: Write cbo.py**

```python
# apps/api/routers/cbo.py
"""
CBO endpoints — ocupações e grupos CBO.
GET /v1/cbo/occupations — top CBO groups by admissões/saldo
"""
import hashlib, json
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
```

**Step 2: Register router in main.py**

Add to `apps/api/main.py` after the existing imports and includes:
```python
from routers import caged, cbo, health, turnover
# ...
app.include_router(cbo.router, prefix="/v1/cbo", tags=["CBO"])
```

**Step 3: Write a smoke test**

Create `apps/api/tests/test_cbo.py`:
```python
"""Tests for GET /v1/cbo/occupations"""
from unittest.mock import AsyncMock, patch
import pytest

def _make_mock_result(rows):
    mock = AsyncMock()
    mock.mappings.return_value.all.return_value = rows
    return mock

def test_cbo_occupations_returns_200(client, mock_db):
    rows = [{"cbo6": "411005", "descricao": "Escriturário", "admissoes": 100,
             "desligamentos": 80, "saldo": 20, "salario_medio": 2500.0}]
    mock_db.execute = AsyncMock(return_value=_make_mock_result(rows))
    r = client.get("/v1/cbo/occupations")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["cbo6"] == "411005"

def test_cbo_occupations_accepts_cnae_filter(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_make_mock_result([]))
    r = client.get("/v1/cbo/occupations?cnae2=47")
    assert r.status_code == 200

def test_cbo_occupations_invalid_cnae(client, mock_db):
    r = client.get("/v1/cbo/occupations?cnae2=999")
    assert r.status_code == 422
```

**Step 4: Run tests**

```bash
cd apps/api && uv run pytest tests/test_cbo.py -v
```
Expected: 3 passed

**Step 5: Commit**

```bash
git add apps/api/routers/cbo.py apps/api/main.py apps/api/tests/test_cbo.py
git commit -m "PW-??: api: add GET /v1/cbo/occupations endpoint"
```

---

### Task 9: Analytics Router (10 endpoints)

**Files:**
- Create: `apps/api/routers/analytics.py`
- Modify: `apps/api/main.py`

**Step 1: Write analytics.py**

```python
# apps/api/routers/analytics.py
"""
Analytics endpoints — Demográfico, Rotatividade, Empresa modules.
Prefix: /v1/analytics
"""
import hashlib, json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db import get_db, get_redis
from routers.caged import _build_where, _uf_to_ibge
from schemas.analytics import (
    CausaDesligamentoResponse, CausaDesligamentoItem,
    EscolaridadeResponse, EscolaridadeItem,
    FaixaEtariaResponse, FaixaEtariaItem,
    GeneroResponse, GeneroItem,
    OcupacaoRankingResponse, OcupacaoRankingItem,
    PorteEmpresaResponse, PorteEmpresaItem,
    TempoEmpregoResponse, TempoEmpregoItem,
    TipoVinculoResponse, TipoVinculoItem,
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
```

**Step 2: Register analytics router in main.py**

```python
from routers import analytics, caged, cbo, health, turnover
# ...
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
```

**Step 3: Write a smoke test**

Create `apps/api/tests/test_analytics.py`:
```python
"""Smoke tests for /v1/analytics endpoints."""
from unittest.mock import AsyncMock

def _mock(rows):
    mock = AsyncMock()
    mock.mappings.return_value.all.return_value = rows
    return mock

def test_genero_returns_200(client, mock_db):
    rows = [{"competencia":"2024-01","sexo":"1","admissoes":100,"desligamentos":80,"saldo":20,"salario_medio":2500.0}]
    mock_db.execute = AsyncMock(return_value=_mock(rows))
    r = client.get("/v1/analytics/demografico/genero")
    assert r.status_code == 200
    assert r.json()["total"] == 1

def test_causas_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_mock([]))
    r = client.get("/v1/analytics/rotatividade/causas")
    assert r.status_code == 200

def test_porte_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_mock([]))
    r = client.get("/v1/analytics/empresa/porte")
    assert r.status_code == 200

def test_ocupacoes_ranking_returns_200(client, mock_db):
    mock_db.execute = AsyncMock(return_value=_mock([]))
    r = client.get("/v1/analytics/ocupacoes/ranking")
    assert r.status_code == 200
```

**Step 4: Run all API tests**

```bash
cd apps/api && uv run pytest tests/ -v
```
Expected: all pass

**Step 5: Commit**

```bash
git add apps/api/routers/analytics.py apps/api/main.py apps/api/tests/test_analytics.py
git commit -m "PW-??: api: add /v1/analytics router (10 endpoints) + /v1/cbo router"
```

---

## Phase 5 — Frontend Module Pages

### Task 10: Add Analytics Types + API Client Functions

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/api-client.ts`

**Step 1: Add types to types.ts**

Append to end of file:
```ts
// ── Analytics types ──────────────────────────────────────────────────────────

export interface GeneroItem {
  competencia: string
  sexo: string  // "1"=M, "3"=F
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface EscolaridadeItem {
  grau_instrucao: number
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface FaixaEtariaItem {
  faixa_etaria: string
  admissoes: number
  desligamentos: number
  saldo: number
}

export interface CausaDesligamentoItem {
  causa_desligamento: number
  desligamentos: number
  salario_medio: number | null
}

export interface TempoEmpregoItem {
  faixa_tempo_emprego: string
  desligamentos: number
}

export interface TipoVinculoItem {
  tipo_vinculo: number
  admissoes: number
  desligamentos: number
  saldo: number
}

export interface PorteEmpresaItem {
  porte_empresa: number
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface OcupacaoItem {
  cbo_grupo: string
  descricao: string | null
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

// Labels for coded fields
export const SEXO_LABELS: Record<string, string> = {
  "1": "Masculino", "3": "Feminino", "9": "Ignorado",
}

export const GRAU_INSTRUCAO_LABELS: Record<number, string> = {
  1: "Analfabeto", 2: "Fundamental incompleto", 3: "Fundamental completo",
  4: "Médio incompleto", 5: "Médio completo", 6: "Superior incompleto",
  7: "Superior completo", 8: "Mestrado", 9: "Doutorado",
}

export const CAUSA_DESLIG_LABELS: Record<number, string> = {
  11: "Sem justa causa", 12: "Com justa causa", 21: "A pedido",
  22: "Aposentadoria", 23: "Transferência", 31: "Término contrato",
  40: "Falecimento", 99: "Outros",
}

export const PORTE_LABELS: Record<number, string> = {
  1: "1–10", 2: "11–50", 3: "51–200", 4: "201–500", 5: "501–1000", 6: "1001+",
}

export const TIPO_VINCULO_LABELS: Record<number, string> = {
  10: "CLT", 15: "CLT doméstico", 20: "Estatutário", 25: "Temporário",
  30: "Avulso", 35: "Aprendiz", 40: "Menor aprendiz", 55: "Outros",
}
```

**Step 2: Add fetch functions to api-client.ts**

Append to end of file:
```ts
// ── Analytics fetch functions ─────────────────────────────────────────────────

function buildAnalyticsParams(filters: Partial<FilterState>): string {
  const params = new URLSearchParams()
  if (filters.cnae2) params.set("cnae2", filters.cnae2)
  if (filters.uf) params.set("uf", filters.uf)
  if (filters.periodo_inicio) params.set("periodo_inicio", filters.periodo_inicio)
  if (filters.periodo_fim) params.set("periodo_fim", filters.periodo_fim)
  return params.toString()
}

async function fetchAnalytics<T>(path: string, filters: Partial<FilterState>): Promise<T> {
  const qs = buildAnalyticsParams(filters)
  const res = await fetchWithTimeout(`${API_BASE}/v1/analytics/${path}${qs ? `?${qs}` : ""}`)
  return res.json()
}

export const fetchDemograficoGenero = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").GeneroItem[]; total: number }>("demografico/genero", f)

export const fetchDemograficoEscolaridade = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").EscolaridadeItem[] }>("demografico/escolaridade", f)

export const fetchDemograficoFaixaEtaria = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").FaixaEtariaItem[] }>("demografico/faixa-etaria", f)

export const fetchRotatividadeCausas = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").CausaDesligamentoItem[] }>("rotatividade/causas", f)

export const fetchRotatividadeTempoEmprego = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").TempoEmpregoItem[] }>("rotatividade/tempo-emprego", f)

export const fetchRotatividadeTipoVinculo = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").TipoVinculoItem[] }>("rotatividade/tipo-vinculo", f)

export const fetchOcupacoesRanking = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").OcupacaoItem[]; total: number }>("ocupacoes/ranking", f)

export const fetchOcupacoesSalario = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").OcupacaoItem[]; total: number }>("ocupacoes/salario", f)

export const fetchEmpresaPorte = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").PorteEmpresaItem[] }>("empresa/porte", f)

export const fetchEmpresaTipoVinculo = (f: Partial<FilterState>) =>
  fetchAnalytics<{ data: import("./types").TipoVinculoItem[] }>("empresa/tipo-vinculo", f)
```

**Step 3: Commit**

```bash
git add apps/web/src/lib/types.ts apps/web/src/lib/api-client.ts
git commit -m "PW-??: feat: add analytics types and API client fetch functions"
```

---

### Task 11: useAnalytics Hook

**Files:**
- Create: `apps/web/src/hooks/useAnalytics.ts`

**Step 1: Write the hook file**

```ts
// apps/web/src/hooks/useAnalytics.ts
"use client"
import { useQuery } from "@tanstack/react-query"
import type { FilterState } from "@/lib/types"
import {
  fetchDemograficoGenero, fetchDemograficoEscolaridade, fetchDemograficoFaixaEtaria,
  fetchRotatividadeCausas, fetchRotatividadeTempoEmprego, fetchRotatividadeTipoVinculo,
  fetchOcupacoesRanking, fetchOcupacoesSalario,
  fetchEmpresaPorte, fetchEmpresaTipoVinculo,
} from "@/lib/api-client"

const STALE = 30 * 60 * 1000

const q = (key: string[], fn: () => Promise<unknown>) =>
  ({ queryKey: key, queryFn: fn, staleTime: STALE, retry: 2 })

export const useDemograficoGenero = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","genero",f], () => fetchDemograficoGenero(f)))

export const useDemograficoEscolaridade = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","escolaridade",f], () => fetchDemograficoEscolaridade(f)))

export const useDemograficoFaixaEtaria = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","faixa_etaria",f], () => fetchDemograficoFaixaEtaria(f)))

export const useRotatividadeCausas = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","causas",f], () => fetchRotatividadeCausas(f)))

export const useRotatividadeTempoEmprego = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","tempo_emprego",f], () => fetchRotatividadeTempoEmprego(f)))

export const useRotatividadeTipoVinculo = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","vinculo_rotat",f], () => fetchRotatividadeTipoVinculo(f)))

export const useOcupacoesRanking = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","ocup_ranking",f], () => fetchOcupacoesRanking(f)))

export const useOcupacoesSalario = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","ocup_salario",f], () => fetchOcupacoesSalario(f)))

export const useEmpresaPorte = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","porte",f], () => fetchEmpresaPorte(f)))

export const useEmpresaTipoVinculo = (f: Partial<FilterState>) =>
  useQuery(q(["analytics","vinculo_empresa",f], () => fetchEmpresaTipoVinculo(f)))
```

**Step 2: Commit**

```bash
git add apps/web/src/hooks/useAnalytics.ts
git commit -m "PW-??: feat: add useAnalytics hooks for all 4 modules"
```

---

### Task 12: Update Sidebar

**Files:**
- Modify: `apps/web/src/components/layout/Sidebar.tsx`

**Step 1: Add ANÁLISE section with 4 module links**

Import new icons at top:
```ts
import { Users, RefreshCw, Briefcase, Factory } from "lucide-react"
```

Add to `navSections` array after MONITOR:
```ts
{
  title: "ANÁLISE",
  items: [
    { label: "Demográfico", href: "/dashboard/demografico", icon: Users },
    { label: "Rotatividade", href: "/dashboard/rotatividade", icon: RefreshCw },
    { label: "Ocupações", href: "/dashboard/ocupacoes", icon: Briefcase },
    { label: "Perspectiva Empresa", href: "/dashboard/empresa", icon: Factory },
  ],
},
```

**Step 2: Verify build**

```bash
cd apps/web && npm run build 2>&1 | tail -10
```

**Step 3: Commit**

```bash
git add apps/web/src/components/layout/Sidebar.tsx
git commit -m "PW-??: feat: add ANÁLISE section to sidebar with 4 module links"
```

---

### Task 13: Módulo Demográfico Page

**Files:**
- Create: `apps/web/src/app/dashboard/demografico/page.tsx`
- Create: `apps/web/src/app/dashboard/demografico/DemograficoContent.tsx`

**Step 1: Create page.tsx**

```tsx
// apps/web/src/app/dashboard/demografico/page.tsx
import type { Metadata } from "next"
import { DemograficoContent } from "./DemograficoContent"

export const metadata: Metadata = { title: "Perfil Demográfico — Radar Trabalhista" }

export default function DemograficoPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Perfil Demográfico</h1>
        <p className="text-sm text-slate-500 mt-0.5">Distribuição por gênero, idade e escolaridade</p>
      </div>
      <DemograficoContent />
    </div>
  )
}
```

**Step 2: Create DemograficoContent.tsx**

```tsx
// apps/web/src/app/dashboard/demografico/DemograficoContent.tsx
"use client"
import { useMemo } from "react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { useDemograficoGenero, useDemograficoFaixaEtaria, useDemograficoEscolaridade } from "@/hooks/useAnalytics"
import { useFiltersStore } from "@/store/filters"
import { GRAU_INSTRUCAO_LABELS } from "@/lib/types"

const COLORS = { M: "#3b82f6", F: "#ec4899" }
const DONUT_COLORS = ["#3b82f6","#06b6d4","#10b981","#f59e0b","#ef4444","#8b5cf6","#64748b","#f97316","#14b8a6"]

export function DemograficoContent() {
  const { committedFilters: filters } = useFiltersStore()
  const generoQ = useDemograficoGenero(filters)
  const faixaQ  = useDemograficoFaixaEtaria(filters)
  const escolQ  = useDemograficoEscolaridade(filters)

  // KPIs
  const kpis = useMemo(() => {
    const rows = generoQ.data?.data ?? []
    const fem = rows.filter((r) => r.sexo === "3").reduce((s, r) => s + r.admissoes, 0)
    const total = rows.reduce((s, r) => s + r.admissoes, 0)
    const pctFem = total > 0 ? (fem / total) * 100 : 0
    const saldoF = rows.filter((r) => r.sexo === "3").reduce((s, r) => s + r.saldo, 0)
    const saldoM = rows.filter((r) => r.sexo === "1").reduce((s, r) => s + r.saldo, 0)
    return { pctFem, saldoF, saldoM }
  }, [generoQ.data])

  // Chart data: group by competencia for bar chart
  const generoChartData = useMemo(() => {
    const byMonth: Record<string, { competencia: string; M: number; F: number }> = {}
    for (const r of generoQ.data?.data ?? []) {
      if (!byMonth[r.competencia]) byMonth[r.competencia] = { competencia: r.competencia, M: 0, F: 0 }
      if (r.sexo === "1") byMonth[r.competencia].M += r.admissoes
      if (r.sexo === "3") byMonth[r.competencia].F += r.admissoes
    }
    return Object.values(byMonth).sort((a, b) => a.competencia.localeCompare(b.competencia))
  }, [generoQ.data])

  const faixaData = useMemo(() =>
    (faixaQ.data?.data ?? []).map((r) => ({ name: r.faixa_etaria, admissoes: r.admissoes, saldo: r.saldo })),
    [faixaQ.data])

  const escolData = useMemo(() =>
    (escolQ.data?.data ?? []).map((r) => ({
      name: GRAU_INSTRUCAO_LABELS[r.grau_instrucao] ?? String(r.grau_instrucao),
      value: r.admissoes,
    })),
    [escolQ.data])

  return (
    <div className="space-y-6">
      <FilterBar />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <KPICard title="% Feminino (admissões)" value={kpis.pctFem} suffix="%" trend="neutral" isLoading={generoQ.isLoading} description="Participação feminina no período" />
        <KPICard title="Saldo Feminino" value={kpis.saldoF} trend={kpis.saldoF >= 0 ? "up" : "down"} isLoading={generoQ.isLoading} description="Saldo líquido (F)" />
        <KPICard title="Saldo Masculino" value={kpis.saldoM} trend={kpis.saldoM >= 0 ? "up" : "down"} isLoading={generoQ.isLoading} description="Saldo líquido (M)" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Admissões por Gênero (mensal)</h2>
          {generoQ.isLoading
            ? <div className="h-64 animate-pulse rounded bg-slate-100" />
            : <ResponsiveContainer width="100%" height={256}>
                <BarChart data={generoChartData}>
                  <XAxis dataKey="competencia" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="M" name="Masculino" fill={COLORS.M} radius={[2,2,0,0]} />
                  <Bar dataKey="F" name="Feminino" fill={COLORS.F} radius={[2,2,0,0]} />
                </BarChart>
              </ResponsiveContainer>}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Distribuição por Faixa Etária</h2>
          {faixaQ.isLoading
            ? <div className="h-64 animate-pulse rounded bg-slate-100" />
            : <ResponsiveContainer width="100%" height={256}>
                <BarChart data={faixaData} layout="vertical">
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={56} />
                  <Tooltip />
                  <Bar dataKey="admissoes" name="Admissões" fill="#3b82f6" radius={[0,2,2,0]} />
                </BarChart>
              </ResponsiveContainer>}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Distribuição por Escolaridade</h2>
        {escolQ.isLoading
          ? <div className="h-48 animate-pulse rounded bg-slate-100" />
          : <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={escolData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {escolData.map((_, i) => <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>}
      </div>
    </div>
  )
}
```

**Step 3: Verify build**

```bash
cd apps/web && npm run build 2>&1 | tail -10
```

**Step 4: Commit**

```bash
git add apps/web/src/app/dashboard/demografico/
git commit -m "PW-??: feat: add Módulo Demográfico page (gênero + faixa etária + escolaridade)"
```

---

### Task 14: Módulo Rotatividade Page

**Files:**
- Create: `apps/web/src/app/dashboard/rotatividade/page.tsx`
- Create: `apps/web/src/app/dashboard/rotatividade/RotatividadeContent.tsx`

**Step 1: Create page.tsx**

```tsx
import type { Metadata } from "next"
import { RotatividadeContent } from "./RotatividadeContent"
export const metadata: Metadata = { title: "Rotatividade — Radar Trabalhista" }
export default function RotatividadePage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Rotatividade</h1>
        <p className="text-sm text-slate-500 mt-0.5">Análise de causas de desligamento e tempo de emprego</p>
      </div>
      <RotatividadeContent />
    </div>
  )
}
```

**Step 2: Create RotatividadeContent.tsx**

```tsx
"use client"
import { useMemo } from "react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { useRotatividadeCausas, useRotatividadeTempoEmprego } from "@/hooks/useAnalytics"
import { useFiltersStore } from "@/store/filters"
import { CAUSA_DESLIG_LABELS } from "@/lib/types"

export function RotatividadeContent() {
  const { committedFilters: filters } = useFiltersStore()
  const causasQ = useRotatividadeCausas(filters)
  const tempoQ  = useRotatividadeTempoEmprego(filters)

  const kpis = useMemo(() => {
    const rows = causasQ.data?.data ?? []
    const total = rows.reduce((s, r) => s + r.desligamentos, 0)
    const semCausa = rows.find((r) => r.causa_desligamento === 11)?.desligamentos ?? 0
    const taxa = total > 0 ? (semCausa / total) * 100 : 0
    return { total, taxa }
  }, [causasQ.data])

  const causasData = useMemo(() =>
    (causasQ.data?.data ?? []).slice(0, 8).map((r) => ({
      name: CAUSA_DESLIG_LABELS[r.causa_desligamento] ?? String(r.causa_desligamento),
      desligamentos: r.desligamentos,
    })),
    [causasQ.data])

  const tempoData = useMemo(() =>
    (tempoQ.data?.data ?? []).map((r) => ({
      name: r.faixa_tempo_emprego,
      desligamentos: r.desligamentos,
    })),
    [tempoQ.data])

  return (
    <div className="space-y-6">
      <FilterBar />
      <div className="grid grid-cols-2 gap-4">
        <KPICard title="Total Desligamentos" value={kpis.total} trend="down" isLoading={causasQ.isLoading} description="No período selecionado" />
        <KPICard title="Taxa Sem Justa Causa" value={kpis.taxa} suffix="%" trend="neutral" isLoading={causasQ.isLoading} description="% dos desligamentos" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Desligamentos por Causa</h2>
          {causasQ.isLoading
            ? <div className="h-64 animate-pulse rounded bg-slate-100" />
            : <ResponsiveContainer width="100%" height={256}>
                <BarChart data={causasData} layout="vertical">
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={120} />
                  <Tooltip />
                  <Bar dataKey="desligamentos" fill="#ef4444" radius={[0,2,2,0]} />
                </BarChart>
              </ResponsiveContainer>}
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Desligamentos por Tempo de Emprego</h2>
          {tempoQ.isLoading
            ? <div className="h-64 animate-pulse rounded bg-slate-100" />
            : <ResponsiveContainer width="100%" height={256}>
                <BarChart data={tempoData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="desligamentos" fill="#f59e0b" radius={[2,2,0,0]} />
                </BarChart>
              </ResponsiveContainer>}
        </div>
      </div>
    </div>
  )
}
```

**Step 3: Verify and commit**

```bash
cd apps/web && npm run build 2>&1 | tail -10
git add apps/web/src/app/dashboard/rotatividade/
git commit -m "PW-??: feat: add Módulo Rotatividade page (causas + tempo emprego)"
```

---

### Task 15: Módulo Ocupações Page

**Files:**
- Create: `apps/web/src/app/dashboard/ocupacoes/page.tsx`
- Create: `apps/web/src/app/dashboard/ocupacoes/OcupacoesContent.tsx`

**Step 1: Create page.tsx**

```tsx
import type { Metadata } from "next"
import { OcupacoesContent } from "./OcupacoesContent"
export const metadata: Metadata = { title: "Ocupações — Radar Trabalhista" }
export default function OcupacoesPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Ocupações (CBO)</h1>
        <p className="text-sm text-slate-500 mt-0.5">Ranking de grupos ocupacionais por admissões e salário</p>
      </div>
      <OcupacoesContent />
    </div>
  )
}
```

**Step 2: Create OcupacoesContent.tsx**

```tsx
"use client"
import { useMemo } from "react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { useOcupacoesRanking, useOcupacoesSalario } from "@/hooks/useAnalytics"
import { useFiltersStore } from "@/store/filters"

function formatCurrency(n: number | null) {
  if (n == null) return "—"
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(n)
}

export function OcupacoesContent() {
  const { committedFilters: filters } = useFiltersStore()
  const rankingQ = useOcupacoesRanking(filters)
  const salarioQ = useOcupacoesSalario(filters)

  const topByAdmissoes = useMemo(() =>
    (rankingQ.data?.data ?? []).slice(0, 10).map((r) => ({
      name: r.descricao ?? r.cbo_grupo,
      admissoes: r.admissoes,
      saldo: r.saldo,
    })),
    [rankingQ.data])

  const kpis = useMemo(() => {
    const rows = rankingQ.data?.data ?? []
    const top = rows[0]
    const topSaldo = [...rows].sort((a, b) => b.saldo - a.saldo)[0]
    return { top, topSaldo }
  }, [rankingQ.data])

  return (
    <div className="space-y-6">
      <FilterBar />
      <div className="grid grid-cols-2 gap-4">
        <KPICard title="Top Ocupação (admissões)" value={kpis.top?.admissoes ?? 0} trend="up" isLoading={rankingQ.isLoading} description={kpis.top?.descricao ?? "—"} />
        <KPICard title="Maior Saldo por Grupo" value={kpis.topSaldo?.saldo ?? 0} trend="up" isLoading={rankingQ.isLoading} description={kpis.topSaldo?.descricao ?? "—"} />
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Ranking por Admissões (Top 10 grupos CBO)</h2>
        {rankingQ.isLoading
          ? <div className="h-64 animate-pulse rounded bg-slate-100" />
          : <ResponsiveContainer width="100%" height={256}>
              <BarChart data={topByAdmissoes} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={160} />
                <Tooltip />
                <Bar dataKey="admissoes" fill="#3b82f6" radius={[0,2,2,0]} />
              </BarChart>
            </ResponsiveContainer>}
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Grupos por Salário Médio</h2>
        {salarioQ.isLoading
          ? <div className="h-40 animate-pulse rounded bg-slate-100" />
          : <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="pb-2 text-left text-xs font-semibold text-slate-500">Grupo CBO</th>
                    <th className="pb-2 text-right text-xs font-semibold text-slate-500">Admissões</th>
                    <th className="pb-2 text-right text-xs font-semibold text-slate-500">Saldo</th>
                    <th className="pb-2 text-right text-xs font-semibold text-slate-500">Salário Médio</th>
                  </tr>
                </thead>
                <tbody>
                  {(salarioQ.data?.data ?? []).slice(0, 15).map((r) => (
                    <tr key={r.cbo_grupo} className="border-b border-slate-50">
                      <td className="py-1.5 text-slate-700">{r.descricao ?? r.cbo_grupo}</td>
                      <td className="py-1.5 text-right text-slate-600">{r.admissoes.toLocaleString("pt-BR")}</td>
                      <td className={`py-1.5 text-right font-medium ${r.saldo >= 0 ? "text-emerald-600" : "text-red-600"}`}>{r.saldo >= 0 ? "+" : ""}{r.saldo.toLocaleString("pt-BR")}</td>
                      <td className="py-1.5 text-right text-slate-500">{formatCurrency(r.salario_medio)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>}
      </div>
    </div>
  )
}
```

**Step 3: Verify and commit**

```bash
cd apps/web && npm run build 2>&1 | tail -10
git add apps/web/src/app/dashboard/ocupacoes/
git commit -m "PW-??: feat: add Módulo Ocupações (CBO) page"
```

---

### Task 16: Módulo Empresa Page

**Files:**
- Create: `apps/web/src/app/dashboard/empresa/page.tsx`
- Create: `apps/web/src/app/dashboard/empresa/EmpresaContent.tsx`

**Step 1: Create page.tsx**

```tsx
import type { Metadata } from "next"
import { EmpresaContent } from "./EmpresaContent"
export const metadata: Metadata = { title: "Perspectiva Empresa — Radar Trabalhista" }
export default function EmpresaPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Perspectiva Empresa</h1>
        <p className="text-sm text-slate-500 mt-0.5">Admissões e demissões por porte e tipo de vínculo</p>
      </div>
      <EmpresaContent />
    </div>
  )
}
```

**Step 2: Create EmpresaContent.tsx**

```tsx
"use client"
import { useMemo } from "react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from "recharts"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { useEmpresaPorte, useEmpresaTipoVinculo } from "@/hooks/useAnalytics"
import { useFiltersStore } from "@/store/filters"
import { PORTE_LABELS, TIPO_VINCULO_LABELS } from "@/lib/types"

export function EmpresaContent() {
  const { committedFilters: filters } = useFiltersStore()
  const porteQ   = useEmpresaPorte(filters)
  const vinculoQ = useEmpresaTipoVinculo(filters)

  const kpis = useMemo(() => {
    const rows = porteQ.data?.data ?? []
    const total = rows.reduce((s, r) => s + r.admissoes, 0)
    const micro = rows.find((r) => r.porte_empresa === 1)?.admissoes ?? 0
    const pctMicro = total > 0 ? (micro / total) * 100 : 0
    const dominant = [...rows].sort((a, b) => b.admissoes - a.admissoes)[0]
    return { pctMicro, dominant }
  }, [porteQ.data])

  const porteData = useMemo(() =>
    (porteQ.data?.data ?? []).map((r) => ({
      name: PORTE_LABELS[r.porte_empresa] ?? String(r.porte_empresa),
      admissoes: r.admissoes,
      desligamentos: r.desligamentos,
      salario_medio: r.salario_medio ?? 0,
    })),
    [porteQ.data])

  const vinculoData = useMemo(() =>
    (vinculoQ.data?.data ?? []).map((r) => ({
      name: TIPO_VINCULO_LABELS[r.tipo_vinculo] ?? String(r.tipo_vinculo),
      admissoes: r.admissoes,
      desligamentos: r.desligamentos,
    })),
    [vinculoQ.data])

  return (
    <div className="space-y-6">
      <FilterBar />
      <div className="grid grid-cols-2 gap-4">
        <KPICard title="% Admissões Micro (≤10)" value={kpis.pctMicro} suffix="%" trend="neutral" isLoading={porteQ.isLoading} description="Empresas com até 10 funcionários" />
        <KPICard title="Porte Dominante" value={kpis.dominant ? kpis.dominant.admissoes : 0} trend="up" isLoading={porteQ.isLoading} description={kpis.dominant ? PORTE_LABELS[kpis.dominant.porte_empresa] : "—"} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Admissões e Demissões por Porte</h2>
          {porteQ.isLoading
            ? <div className="h-64 animate-pulse rounded bg-slate-100" />
            : <ResponsiveContainer width="100%" height={256}>
                <BarChart data={porteData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="admissoes" name="Admissões" fill="#3b82f6" radius={[2,2,0,0]} />
                  <Bar dataKey="desligamentos" name="Demissões" fill="#ef4444" radius={[2,2,0,0]} />
                </BarChart>
              </ResponsiveContainer>}
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Salário Médio por Porte</h2>
          {porteQ.isLoading
            ? <div className="h-64 animate-pulse rounded bg-slate-100" />
            : <ResponsiveContainer width="100%" height={256}>
                <LineChart data={porteData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="salario_medio" stroke="#10b981" strokeWidth={2} dot />
                </LineChart>
              </ResponsiveContainer>}
        </div>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Mix por Tipo de Vínculo</h2>
        {vinculoQ.isLoading
          ? <div className="h-48 animate-pulse rounded bg-slate-100" />
          : <ResponsiveContainer width="100%" height={200}>
              <BarChart data={vinculoData} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={100} />
                <Tooltip />
                <Legend />
                <Bar dataKey="admissoes" name="Admissões" fill="#3b82f6" radius={[0,2,2,0]} />
                <Bar dataKey="desligamentos" name="Demissões" fill="#ef4444" radius={[0,2,2,0]} />
              </BarChart>
            </ResponsiveContainer>}
      </div>
    </div>
  )
}
```

**Step 3: Final build verification**

```bash
cd apps/web && npm run build 2>&1 | tail -20
```
Expected: all 10 routes compile, no type errors.

**Step 4: Final commit**

```bash
git add apps/web/src/app/dashboard/empresa/
git commit -m "PW-??: feat: add Módulo Empresa page (porte + vínculo + salário)"
```

---

## Summary

| Phase | Tasks | What changes |
|-------|-------|--------------|
| 1 | 1–4 | `filters.ts`, `useCaged.ts`, `FilterBar.tsx`, `DashboardContent.tsx`, `MapaUFInner.tsx`, new `TabelaEvolucaoMensal.tsx` |
| 2 | 5 | New `migrations/001_analytics_tables.sql` |
| 3 | 6 | New `etl/bq_backfill_dims.py` |
| 4 | 7–9 | New `schemas/analytics.py`, `routers/cbo.py`, `routers/analytics.py`, updated `main.py`, 2 test files |
| 5 | 10–16 | Updated `types.ts`, `api-client.ts`, new `hooks/useAnalytics.ts`, updated `Sidebar.tsx`, 4 new module page directories |

**Total new files:** 14
**Files modified:** 7
**New API endpoints:** 11 (`/v1/cbo/occupations` + 10 `/v1/analytics/*`)
**New frontend pages:** 4 (`/dashboard/demografico`, `/dashboard/rotatividade`, `/dashboard/ocupacoes`, `/dashboard/empresa`)
