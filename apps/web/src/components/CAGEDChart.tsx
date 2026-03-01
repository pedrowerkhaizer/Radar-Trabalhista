"use client"
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import type { CAGEDSummaryItem } from "@/lib/types"

interface CAGEDChartProps {
  data: CAGEDSummaryItem[]
  isLoading?: boolean
}

const ADMISSOES_COLOR = "#60A5FA"  // blue-400
const DESLIGAMENTOS_COLOR = "#FDA4AF"  // rose-300
const SALDO_COLOR = "#2563EB"  // blue-600
const AXIS_COLOR = "#94A3B8"  // slate-400

const fmt = (v: number) => v.toLocaleString("pt-BR")

export function CAGEDChart({ data, isLoading }: CAGEDChartProps) {
  if (isLoading) return <Skeleton className="h-80 w-full" />

  const chartData = data.map((d) => ({
    mes: d.competencia,
    Admissões: d.admissoes,
    Desligamentos: d.desligamentos,
    Saldo: d.saldo,
  }))

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#F1F5F9"
            vertical={false}
          />
          <XAxis
            dataKey="mes"
            tick={{ fontSize: 12, fill: AXIS_COLOR }}
            axisLine={{ stroke: "#E2E8F0" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={fmt}
            tick={{ fontSize: 12, fill: AXIS_COLOR }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: number) => fmt(value)}
            contentStyle={{
              borderRadius: "8px",
              border: "1px solid #E2E8F0",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.07)",
              fontSize: "12px",
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: "12px", color: AXIS_COLOR }}
          />
          <Bar
            dataKey="Admissões"
            fill={ADMISSOES_COLOR}
            opacity={0.85}
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Desligamentos"
            fill={DESLIGAMENTOS_COLOR}
            opacity={0.85}
            radius={[3, 3, 0, 0]}
          />
          <Line
            type="monotone"
            dataKey="Saldo"
            stroke={SALDO_COLOR}
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
