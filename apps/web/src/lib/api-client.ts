import type { CAGEDSummaryResponse, CAGEDSeriesResponse, CBOItem, FilterState } from "./types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const TIMEOUT_MS = 10_000

async function fetchWithTimeout(url: string): Promise<Response> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(url, { signal: controller.signal })
    if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`)
    return res
  } finally {
    clearTimeout(timeout)
  }
}

function buildParams(filters: Partial<FilterState>): string {
  const params = new URLSearchParams()
  if (filters.cnae2) params.set("cnae2", filters.cnae2)
  if (filters.uf) params.set("uf", filters.uf)
  if (filters.periodo_inicio) params.set("periodo_inicio", filters.periodo_inicio)
  if (filters.periodo_fim) params.set("periodo_fim", filters.periodo_fim)
  return params.toString()
}

export async function fetchCAGEDSummary(filters: Partial<FilterState>): Promise<CAGEDSummaryResponse> {
  const qs = buildParams(filters)
  const res = await fetchWithTimeout(`${API_BASE}/v1/caged/summary${qs ? `?${qs}` : ""}`)
  return res.json()
}

export async function fetchCAGEDSeries(filters: Partial<FilterState>, meses = 12): Promise<CAGEDSeriesResponse> {
  const qs = buildParams(filters)
  const url = `${API_BASE}/v1/caged/series?meses=${meses}${qs ? `&${qs}` : ""}`
  const res = await fetchWithTimeout(url)
  return res.json()
}

export async function fetchCBOOccupations(cnae2?: string): Promise<CBOItem[]> {
  const qs = cnae2 ? `?cnae2=${cnae2}` : ""
  const res = await fetchWithTimeout(`${API_BASE}/v1/cbo/occupations${qs}`)
  return res.json()
}
