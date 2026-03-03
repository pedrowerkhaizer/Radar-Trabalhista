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
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(n)
}

export function TabelaEvolucaoMensal({ data, isLoading }: Props) {
  if (isLoading) {
    return <div className="h-48 animate-pulse rounded-lg bg-slate-100" />
  }

  // Sort ascending: oldest → newest
  const rows = [...data].sort((a, b) => a.competencia.localeCompare(b.competencia))

  if (rows.length === 0) {
    return (
      <p className="text-sm text-slate-400 text-center py-8">
        Sem dados para o período selecionado.
      </p>
    )
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
            <tr
              key={row.competencia}
              className="border-b border-slate-50 hover:bg-slate-50 transition-colors"
            >
              <td className="py-1.5 font-medium text-slate-700">{row.competencia}</td>
              <td className="py-1.5 text-right text-slate-600">{formatNum(row.admissoes)}</td>
              <td className="py-1.5 text-right text-slate-600">{formatNum(row.desligamentos)}</td>
              <td
                className={cn(
                  "py-1.5 text-right font-semibold",
                  row.saldo >= 0 ? "text-emerald-600" : "text-red-600"
                )}
              >
                {row.saldo >= 0 ? "+" : ""}
                {formatNum(row.saldo)}
              </td>
              <td className="py-1.5 text-right text-slate-500">
                {formatCurrency(row.salario_medio)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
