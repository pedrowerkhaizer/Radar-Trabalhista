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
                  <Bar dataKey="desligamentos" fill="#ef4444" radius={[0, 2, 2, 0]} />
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
                  <Bar dataKey="desligamentos" fill="#f59e0b" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>}
        </div>
      </div>
    </div>
  )
}
