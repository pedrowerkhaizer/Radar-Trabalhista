"use client"
import { Suspense } from "react"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { CAGEDChart } from "@/components/CAGEDChart"
import { SetorRanking } from "@/components/SetorRanking"
import { MapaUF } from "@/components/MapaUF"
import { useCagedSummary, useCagedSeries } from "@/hooks/useCaged"
import { useFiltersStore } from "@/store/filters"

function DashboardContent() {
  const { filters } = useFiltersStore()
  const summaryQuery = useCagedSummary(filters)
  const seriesQuery = useCagedSeries(filters, filters.meses)

  const latest = summaryQuery.data?.data?.[0]
  const sparkline = seriesQuery.data?.series?.map(s => s.saldo) ?? []

  return (
    <div className="space-y-6">
      <FilterBar />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Saldo Líquido"
          value={latest?.saldo ?? 0}
          trend={latest && latest.saldo >= 0 ? "up" : "down"}
          sparklineData={sparkline}
          isLoading={summaryQuery.isLoading}
        />
        <KPICard
          title="Admissões"
          value={latest?.admissoes ?? 0}
          trend="up"
          isLoading={summaryQuery.isLoading}
        />
        <KPICard
          title="Demissões"
          value={latest?.desligamentos ?? 0}
          trend="down"
          isLoading={summaryQuery.isLoading}
        />
        <KPICard
          title="Salário Médio"
          value={latest?.salario_medio ?? 0}
          prefix="R$ "
          trend="neutral"
          isLoading={summaryQuery.isLoading}
        />
      </div>

      {/* Gráfico */}
      <div className="bg-card border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4">Evolução Mensal</h2>
        <CAGEDChart data={seriesQuery.data?.series ?? []} isLoading={seriesQuery.isLoading} />
      </div>

      {/* Mapa + Ranking */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-card border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Mapa por UF</h2>
          <MapaUF data={summaryQuery.data?.data ?? []} isLoading={summaryQuery.isLoading} />
        </div>
        <div className="bg-card border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Ranking por Período</h2>
          <SetorRanking data={summaryQuery.data?.data ?? []} isLoading={summaryQuery.isLoading} />
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Monitor de Mercado de Trabalho</h1>
        <p className="text-muted-foreground">Dados CAGED — atualização mensal</p>
      </div>
      <Suspense fallback={<div>Carregando...</div>}>
        <DashboardContent />
      </Suspense>
    </div>
  )
}
