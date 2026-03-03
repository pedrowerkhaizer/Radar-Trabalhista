"use client"
import { useMemo } from "react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { FilterBar } from "@/components/FilterBar"
import { KPICard } from "@/components/KPICard"
import { useDemograficoGenero, useDemograficoFaixaEtaria, useDemograficoEscolaridade } from "@/hooks/useAnalytics"
import { useFiltersStore } from "@/store/filters"
import { GRAU_INSTRUCAO_LABELS } from "@/lib/types"

const COLORS = { M: "#3b82f6", F: "#ec4899" }
const DONUT_COLORS = ["#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b", "#f97316", "#14b8a6"]

export function DemograficoContent() {
  const { committedFilters: filters } = useFiltersStore()
  const generoQ = useDemograficoGenero(filters)
  const faixaQ  = useDemograficoFaixaEtaria(filters)
  const escolQ  = useDemograficoEscolaridade(filters)

  const kpis = useMemo(() => {
    const rows = generoQ.data?.data ?? []
    const fem = rows.filter((r) => r.sexo === "3").reduce((s, r) => s + r.admissoes, 0)
    const total = rows.reduce((s, r) => s + r.admissoes, 0)
    const pctFem = total > 0 ? (fem / total) * 100 : 0
    const saldoF = rows.filter((r) => r.sexo === "3").reduce((s, r) => s + r.saldo, 0)
    const saldoM = rows.filter((r) => r.sexo === "1").reduce((s, r) => s + r.saldo, 0)
    return { pctFem, saldoF, saldoM }
  }, [generoQ.data])

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
                  <Bar dataKey="M" name="Masculino" fill={COLORS.M} radius={[2, 2, 0, 0]} />
                  <Bar dataKey="F" name="Feminino" fill={COLORS.F} radius={[2, 2, 0, 0]} />
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
                  <Bar dataKey="admissoes" name="Admissões" fill="#3b82f6" radius={[0, 2, 2, 0]} />
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
