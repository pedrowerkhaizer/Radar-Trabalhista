"use client"
import { useMemo } from "react"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { CAGEDChart } from "@/components/CAGEDChart"
import { SetorRanking } from "@/components/SetorRanking"
import { MapaUF } from "@/components/MapaUF"
import { useCagedSummary, useCagedSeries, useCagedMap } from "@/hooks/useCaged"
import { useFiltersStore } from "@/store/filters"

export function DashboardContent() {
  const { committedFilters: filters } = useFiltersStore()
  const summaryQuery = useCagedSummary(filters)
  const seriesQuery = useCagedSeries(filters, filters.meses)
  const mapQuery = useCagedMap(filters)
  const totals = useMemo(() => {
    const rows = summaryQuery.data?.data ?? []
    if (rows.length === 0) return null
    const salaryRows = rows.filter((r) => r.salario_medio !== null)
    return {
      admissoes:     rows.reduce((s, r) => s + r.admissoes, 0),
      desligamentos: rows.reduce((s, r) => s + r.desligamentos, 0),
      saldo:         rows.reduce((s, r) => s + r.saldo, 0),
      // saldoDelta: last month vs previous month (recent trend direction)
      // rows[0]=newest month, rows[1]=previous month (DESC order)
      saldoDelta: rows.length > 1
        ? ((rows[0].saldo - rows[1].saldo) / Math.max(Math.abs(rows[1].saldo), 1)) * 100
        : 0,
      salario_medio: salaryRows.length > 0
        ? salaryRows.reduce((s, r) => s + r.salario_medio!, 0) / salaryRows.length
        : null,
    }
  }, [summaryQuery.data])
  const sparkline = seriesQuery.data?.series?.map((s) => s.saldo) ?? []

  return (
    <div className="space-y-6">
      <FilterBar />

      {/* KPI Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KPICard
          title="Saldo Líquido"
          value={totals?.saldo ?? 0}
          delta={totals?.saldoDelta}
          trend={totals && totals.saldo >= 0 ? "up" : "down"}
          sparklineData={sparkline}
          isLoading={summaryQuery.isLoading}
          description="Admissões − Demissões no período"
        />
        <KPICard
          title="Admissões"
          value={totals?.admissoes ?? 0}
          trend="up"
          isLoading={summaryQuery.isLoading}
          description="Total no período"
        />
        <KPICard
          title="Demissões"
          value={totals?.desligamentos ?? 0}
          trend="down"
          isLoading={summaryQuery.isLoading}
          description="Total no período"
        />
        <KPICard
          title="Salário Médio"
          value={totals?.salario_medio ?? 0}
          prefix="R$ "
          trend="neutral"
          isLoading={summaryQuery.isLoading}
          description="Média das admissões"
        />
      </div>

      {/* Chart */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Evolução Mensal</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Admissões, demissões e saldo líquido
            </p>
          </div>
        </div>
        <CAGEDChart
          data={seriesQuery.data?.series ?? []}
          isLoading={seriesQuery.isLoading}
        />
      </div>

      {/* Map + Ranking */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">
            Distribuição por UF
          </h2>
          <MapaUF
            data={mapQuery.data?.data ?? []}
            isLoading={mapQuery.isLoading}
          />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">
            Ranking por Competência
          </h2>
          <SetorRanking
            data={summaryQuery.data?.data ?? []}
            isLoading={summaryQuery.isLoading}
          />
        </div>
      </div>
    </div>
  )
}
