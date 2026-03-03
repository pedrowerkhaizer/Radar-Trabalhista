"use client"
import { useQuery } from "@tanstack/react-query"
import { fetchCAGEDSummary, fetchCAGEDSeries, fetchCAGEDMap } from "@/lib/api-client"
import type { FilterState } from "@/lib/types"

const STALE_TIME = 30 * 60 * 1000 // 30 minutes — CAGED is monthly data

export function useCagedSummary(filters: Partial<FilterState>) {
  return useQuery({
    queryKey: ["caged", "summary", filters],
    queryFn: () => fetchCAGEDSummary(filters),
    staleTime: STALE_TIME,
    retry: 2,
  })
}

export function useCagedSeries(filters: Partial<FilterState>, meses = 12) {
  return useQuery({
    queryKey: ["caged", "series", filters, meses],
    queryFn: () => fetchCAGEDSeries(filters, meses),
    staleTime: STALE_TIME,
    retry: 2,
    // When a custom date range is active, /summary already covers this data
    enabled: !filters.periodo_inicio,
  })
}

export function useCagedMap(filters: Partial<FilterState>) {
  return useQuery({
    queryKey: ["caged", "map", filters],
    queryFn: () => fetchCAGEDMap(filters),
    staleTime: STALE_TIME,
    retry: 2,
  })
}
