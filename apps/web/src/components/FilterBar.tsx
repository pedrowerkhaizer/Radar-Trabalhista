"use client"
import { useRouter, useSearchParams, usePathname } from "next/navigation"
import { useCallback } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { CNAE_OPTIONS, UF_OPTIONS } from "@/lib/types"
import { useFiltersStore } from "@/store/filters"

export function FilterBar() {
  const { filters, setFilter, resetFilters } = useFiltersStore()
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const updateURL = useCallback((key: string, value: string | undefined) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value) { params.set(key, value) } else { params.delete(key) }
    router.replace(`${pathname}?${params.toString()}`, { scroll: false })
  }, [router, pathname, searchParams])

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 bg-card border rounded-lg">
      <Select
        value={filters.cnae2 ?? ""}
        onValueChange={(v) => { setFilter("cnae2", v || undefined); updateURL("cnae2", v || undefined) }}
      >
        <SelectTrigger className="w-[200px]" aria-label="Filtrar por setor CNAE">
          <SelectValue placeholder="Setor (CNAE)" />
        </SelectTrigger>
        <SelectContent>
          {CNAE_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.uf ?? ""}
        onValueChange={(v) => { setFilter("uf", v || undefined); updateURL("uf", v || undefined) }}
      >
        <SelectTrigger className="w-[160px]" aria-label="Filtrar por estado UF">
          <SelectValue placeholder="Estado (UF)" />
        </SelectTrigger>
        <SelectContent>
          {UF_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={String(filters.meses)}
        onValueChange={(v) => { setFilter("meses", Number(v)); updateURL("meses", v) }}
      >
        <SelectTrigger className="w-[140px]" aria-label="Filtrar por período">
          <SelectValue placeholder="Período" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="3">Últimos 3 meses</SelectItem>
          <SelectItem value="12">Últimos 12 meses</SelectItem>
          <SelectItem value="24">Últimos 24 meses</SelectItem>
          <SelectItem value="60">Últimos 60 meses</SelectItem>
        </SelectContent>
      </Select>

      {(filters.cnae2 || filters.uf) && (
        <Button variant="ghost" size="sm" onClick={() => { resetFilters(); router.replace(pathname) }} aria-label="Limpar todos os filtros">
          <X className="h-4 w-4 mr-1" /> Limpar
        </Button>
      )}
    </div>
  )
}
