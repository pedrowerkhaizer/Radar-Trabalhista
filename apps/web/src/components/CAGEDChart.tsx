"use client"
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import type { CAGEDSummaryItem } from "@/lib/types"

interface CAGEDChartProps {
  data: CAGEDSummaryItem[]
  isLoading?: boolean
}

const fmt = (v: number) => v.toLocaleString("pt-BR")

export function CAGEDChart({ data, isLoading }: CAGEDChartProps) {
  if (isLoading) return <Skeleton className="h-80 w-full" />

  const chartData = data.map(d => ({
    mes: d.competencia,
    Admissões: d.admissoes,
    Desligamentos: d.desligamentos,
    Saldo: d.saldo,
  }))

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value: number) => fmt(value)} />
          <Legend />
          <Bar dataKey="Admissões" fill="#22c55e" opacity={0.85} />
          <Bar dataKey="Desligamentos" fill="#ef4444" opacity={0.85} />
          <Line type="monotone" dataKey="Saldo" stroke="#3b82f6" strokeWidth={2} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
