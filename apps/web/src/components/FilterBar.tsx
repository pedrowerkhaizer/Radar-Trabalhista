"use client"
import { useFiltersStore } from "@/store/filters"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { CNAE_OPTIONS, UF_OPTIONS } from "@/lib/types"
import { Filter, X } from "lucide-react"

export function FilterBar() {
  const { filters, setFilter, resetFilters, commitFilters } = useFiltersStore()
  const router = useRouter()

  useEffect(() => {
    const params = new URLSearchParams()
    if (filters.cnae2) {
      params.set("cnae2", filters.cnae2)
    } else {
      params.delete("cnae2")
    }
    if (filters.uf) {
      params.set("uf", filters.uf)
    } else {
      params.delete("uf")
    }
    if (filters.meses !== 12) {
      params.set("meses", String(filters.meses))
    } else {
      params.delete("meses")
    }
    router.replace(`?${params.toString()}`, { scroll: false })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, router])

  // Debounce: commit to query keys after 400ms of inactivity
  useEffect(() => {
    const timer = setTimeout(() => {
      commitFilters()
    }, 400)
    return () => clearTimeout(timer)
  }, [filters, commitFilters])

  const hasActiveFilters =
    filters.cnae2 || filters.uf || filters.meses !== 12

  function clearFilters() {
    resetFilters()
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
        <Filter className="h-3.5 w-3.5" />
        <span>Filtros</span>
      </div>

      <select
        value={filters.cnae2 ?? ""}
        onChange={(e) => setFilter("cnae2", e.target.value || undefined)}
        className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-50"
        aria-label="Filtrar por setor CNAE"
      >
        <option value="">Todos os setores</option>
        {CNAE_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      <select
        value={filters.uf ?? ""}
        onChange={(e) => setFilter("uf", e.target.value || undefined)}
        className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-50"
        aria-label="Filtrar por estado UF"
      >
        <option value="">Todos os estados</option>
        {UF_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      <select
        value={filters.meses}
        onChange={(e) => setFilter("meses", Number(e.target.value))}
        className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-50"
        aria-label="Filtrar por período"
      >
        <option value={3}>Últimos 3 meses</option>
        <option value={6}>Últimos 6 meses</option>
        <option value={12}>Últimos 12 meses</option>
        <option value={24}>Últimos 24 meses</option>
      </select>

      {hasActiveFilters && (
        <button
          onClick={clearFilters}
          className="flex items-center gap-1 rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 transition-colors"
          aria-label="Limpar todos os filtros"
        >
          <X className="h-3 w-3" />
          Limpar
        </button>
      )}
    </div>
  )
}
