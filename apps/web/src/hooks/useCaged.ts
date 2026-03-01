"use client"
import { useQuery } from "@tanstack/react-query"
import { fetchCAGEDSummary, fetchCAGEDSeries } from "@/lib/api-client"
import type { FilterState } from "@/lib/types"

export function useCagedSummary(filters: Partial<FilterState>) {
  return useQuery({
    queryKey: ["caged", "summary", filters],
    queryFn: () => fetchCAGEDSummary(filters),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}

export function useCagedSeries(filters: Partial<FilterState>, meses = 12) {
  return useQuery({
    queryKey: ["caged", "series", filters, meses],
    queryFn: () => fetchCAGEDSeries(filters, meses),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}
