"use client"
import { Skeleton } from "@/components/ui/skeleton"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { LineChart, Line, ResponsiveContainer } from "recharts"
import { cn } from "@/lib/utils"

interface KPICardProps {
  title: string
  value: string | number
  delta?: number
  trend?: "up" | "down" | "neutral"
  sparklineData?: number[]
  isLoading?: boolean
  prefix?: string
  suffix?: string
  description?: string
}

export function KPICard({
  title,
  value,
  delta,
  trend = "neutral",
  sparklineData,
  isLoading,
  prefix,
  suffix,
  description,
}: KPICardProps) {
  if (isLoading)
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
        <Skeleton className="h-3.5 w-24 mb-3" />
        <Skeleton className="h-8 w-32 mb-1.5" />
        <Skeleton className="h-3 w-16 mb-4" />
        <Skeleton className="h-10 w-full" />
      </div>
    )

  const deltaConfig = {
    up: {
      icon: TrendingUp,
      bg: "bg-emerald-50",
      text: "text-emerald-700",
      sparkColor: "#059669",
    },
    down: {
      icon: TrendingDown,
      bg: "bg-red-50",
      text: "text-red-700",
      sparkColor: "#DC2626",
    },
    neutral: {
      icon: Minus,
      bg: "bg-slate-100",
      text: "text-slate-500",
      sparkColor: "#94A3B8",
    },
  }[trend]

  const formattedValue =
    typeof value === "number"
      ? value.toLocaleString(
          "pt-BR",
          prefix === "R$ "
            ? { minimumFractionDigits: 2, maximumFractionDigits: 2 }
            : {}
        )
      : value

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card transition-shadow hover:shadow-card-hover">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        {delta !== undefined && (
          <span
            className={cn(
              "flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold",
              deltaConfig.bg,
              deltaConfig.text
            )}
          >
            <deltaConfig.icon className="h-3 w-3" />
            {Math.abs(delta).toFixed(1)}%
          </span>
        )}
      </div>

      <div className="mt-2">
        <p className="text-3xl font-bold tracking-tight text-slate-900">
          {prefix}
          {formattedValue}
          {suffix}
        </p>
        {description && (
          <p className="mt-0.5 text-xs text-slate-400">{description}</p>
        )}
      </div>

      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-4 h-12">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData.map((v, i) => ({ v, i }))}>
              <Line
                type="monotone"
                dataKey="v"
                dot={false}
                strokeWidth={2}
                stroke={deltaConfig.sparkColor}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
