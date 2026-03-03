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
  type TooltipProps,
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
const SALARIO_COLOR = "#10b981"  // emerald-500
const AXIS_COLOR = "#94A3B8"  // slate-400

const fmt = (v: number) => v.toLocaleString("pt-BR")
const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(v)

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ borderRadius: 8, border: "1px solid #E2E8F0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.07)", background: "#fff", padding: "10px 14px", fontSize: 12 }}>
      <p style={{ fontWeight: 600, marginBottom: 6, color: "#334155" }}>{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color, margin: "2px 0" }}>
          {entry.name}:{" "}
          <span style={{ fontWeight: 500 }}>
            {entry.name === "Salário Médio" ? fmtBRL(entry.value ?? 0) : fmt(entry.value ?? 0)}
          </span>
        </p>
      ))}
    </div>
  )
}

export function CAGEDChart({ data, isLoading }: CAGEDChartProps) {
  if (isLoading) return <Skeleton className="h-80 w-full" />

  const chartData = data.map((d) => ({
    mes: d.competencia,
    Admissões: d.admissoes,
    Desligamentos: d.desligamentos,
    Saldo: d.saldo,
    "Salário Médio": d.salario_medio ?? undefined,
  }))

  const hasSalario = chartData.some((d) => d["Salário Médio"] != null)

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 5, right: hasSalario ? 60 : 20, left: 10, bottom: 5 }}>
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
            yAxisId="left"
            tickFormatter={fmt}
            tick={{ fontSize: 12, fill: AXIS_COLOR }}
            axisLine={false}
            tickLine={false}
          />
          {hasSalario && (
            <YAxis
              yAxisId="right"
              orientation="right"
              tickFormatter={fmtBRL}
              tick={{ fontSize: 11, fill: SALARIO_COLOR }}
              axisLine={false}
              tickLine={false}
              width={72}
            />
          )}
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: "12px", color: AXIS_COLOR }} />
          <Bar
            yAxisId="left"
            dataKey="Admissões"
            fill={ADMISSOES_COLOR}
            opacity={0.85}
            radius={[3, 3, 0, 0]}
          />
          <Bar
            yAxisId="left"
            dataKey="Desligamentos"
            fill={DESLIGAMENTOS_COLOR}
            opacity={0.85}
            radius={[3, 3, 0, 0]}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="Saldo"
            stroke={SALDO_COLOR}
            strokeWidth={2}
            dot={false}
          />
          {hasSalario && (
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="Salário Médio"
              stroke={SALARIO_COLOR}
              strokeWidth={2}
              dot={false}
              strokeDasharray="5 3"
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
