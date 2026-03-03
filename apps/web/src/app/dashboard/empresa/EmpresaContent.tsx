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
                  <Bar dataKey="admissoes" name="Admissões" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="desligamentos" name="Demissões" fill="#ef4444" radius={[2, 2, 0, 0]} />
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
                <Bar dataKey="admissoes" name="Admissões" fill="#3b82f6" radius={[0, 2, 2, 0]} />
                <Bar dataKey="desligamentos" name="Demissões" fill="#ef4444" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>}
      </div>
    </div>
  )
}
