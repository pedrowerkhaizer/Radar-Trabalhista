"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
}

export function KPICard({ title, value, delta, trend = "neutral", sparklineData, isLoading, prefix, suffix }: KPICardProps) {
  if (isLoading) return (
    <Card>
      <CardHeader className="pb-2"><Skeleton className="h-4 w-24" /></CardHeader>
      <CardContent><Skeleton className="h-8 w-32 mb-2" /><Skeleton className="h-4 w-16" /></CardContent>
    </Card>
  )

  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus
  const trendColor = trend === "up" ? "text-green-600" : trend === "down" ? "text-red-600" : "text-gray-500"
  const badgeVariant = trend === "up" ? "default" : trend === "down" ? "destructive" : "secondary"

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {prefix}{typeof value === "number" ? value.toLocaleString("pt-BR") : value}{suffix}
        </div>
        {delta !== undefined && (
          <div className="flex items-center gap-1 mt-1">
            <TrendIcon className={cn("h-4 w-4", trendColor)} />
            <Badge variant={badgeVariant} className="text-xs">
              {delta > 0 ? "+" : ""}{delta.toFixed(1)}%
            </Badge>
          </div>
        )}
        {sparklineData && sparklineData.length > 0 && (
          <div className="h-10 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sparklineData.map((v, i) => ({ v, i }))}>
                <Line type="monotone" dataKey="v" dot={false} strokeWidth={1.5}
                  stroke={trend === "up" ? "#16a34a" : trend === "down" ? "#dc2626" : "#6b7280"} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
