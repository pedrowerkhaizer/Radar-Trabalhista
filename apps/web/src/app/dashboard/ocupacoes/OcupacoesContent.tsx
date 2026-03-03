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
                <Bar dataKey="admissoes" fill="#3b82f6" radius={[0, 2, 2, 0]} />
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
