"use client"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { CAGEDChart } from "@/components/CAGEDChart"
import { SetorRanking } from "@/components/SetorRanking"
import { MapaUF } from "@/components/MapaUF"
import { useCagedSummary, useCagedSeries } from "@/hooks/useCaged"
import { useFiltersStore } from "@/store/filters"

export function DashboardContent() {
  const { filters } = useFiltersStore()
  const summaryQuery = useCagedSummary(filters)
  const seriesQuery = useCagedSeries(filters, filters.meses)
  const latest = summaryQuery.data?.data?.[0]
  const sparkline = seriesQuery.data?.series?.map((s) => s.saldo) ?? []

  return (
    <div className="space-y-6">
      <FilterBar />

      {/* KPI Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KPICard
          title="Saldo Líquido"
          value={latest?.saldo ?? 0}
          delta={
            latest
              ? (latest.saldo / Math.max(latest.admissoes, 1)) * 100
              : undefined
          }
          trend={latest && latest.saldo >= 0 ? "up" : "down"}
          sparklineData={sparkline}
          isLoading={summaryQuery.isLoading}
          description="Admissões − Demissões"
        />
        <KPICard
          title="Admissões"
          value={latest?.admissoes ?? 0}
          trend="up"
          isLoading={summaryQuery.isLoading}
          description="Total no período"
        />
        <KPICard
          title="Demissões"
          value={latest?.desligamentos ?? 0}
          trend="down"
          isLoading={summaryQuery.isLoading}
          description="Total no período"
        />
        <KPICard
          title="Salário Médio"
          value={latest?.salario_medio ?? 0}
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
            data={summaryQuery.data?.data ?? []}
            isLoading={summaryQuery.isLoading}
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
