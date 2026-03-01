"use client"
import {
  useReactTable, getCoreRowModel, getSortedRowModel,
  getFilteredRowModel, flexRender,
  type ColumnDef, type SortingState,
} from "@tanstack/react-table"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Download, ArrowUpDown } from "lucide-react"
import type { CAGEDSummaryItem } from "@/lib/types"

interface SetorRankingProps {
  data: CAGEDSummaryItem[]
  isLoading?: boolean
}

function exportCSV(data: CAGEDSummaryItem[]) {
  const header = "competencia,admissoes,desligamentos,saldo,salario_medio\n"
  const rows = data.map(r =>
    `${r.competencia},${r.admissoes},${r.desligamentos},${r.saldo},${r.salario_medio ?? ""}`
  ).join("\n")
  const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a"); a.href = url; a.download = "caged_ranking.csv"; a.click()
  URL.revokeObjectURL(url)
}

export function SetorRanking({ data, isLoading }: SetorRankingProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: "saldo", desc: true }])
  const [globalFilter, setGlobalFilter] = useState("")

  const columns: ColumnDef<CAGEDSummaryItem>[] = [
    { accessorKey: "competencia", header: "Competência" },
    { accessorKey: "admissoes", header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting()} aria-label="Ordenar por admissões">
        Admissões <ArrowUpDown className="ml-1 h-4 w-4" />
      </Button>
    ), cell: ({ getValue }) => (getValue() as number).toLocaleString("pt-BR") },
    { accessorKey: "desligamentos", header: "Demissões",
      cell: ({ getValue }) => (getValue() as number).toLocaleString("pt-BR") },
    { accessorKey: "saldo", header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting()} aria-label="Ordenar por saldo">
        Saldo <ArrowUpDown className="ml-1 h-4 w-4" />
      </Button>
    ), cell: ({ getValue }) => {
      const v = getValue() as number
      return <span className={v >= 0 ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
        {v >= 0 ? "+" : ""}{v.toLocaleString("pt-BR")}
      </span>
    }},
    { accessorKey: "salario_medio", header: "Salário Médio",
      cell: ({ getValue }) => {
        const v = getValue() as number | null
        return v ? `R$ ${v.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}` : "—"
      }},
  ]

  const table = useReactTable({
    data, columns, state: { sorting, globalFilter },
    onSortingChange: setSorting, onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  if (isLoading) return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
    </div>
  )

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Input placeholder="Buscar..." value={globalFilter} onChange={(e) => setGlobalFilter(e.target.value)}
          className="max-w-xs" aria-label="Buscar na tabela" />
        <Button variant="outline" size="sm" onClick={() => exportCSV(data)} aria-label="Exportar dados em CSV">
          <Download className="h-4 w-4 mr-1" /> Exportar CSV
        </Button>
      </div>
      <div className="rounded-md border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(h => (
                  <th key={h.id} className="px-4 py-3 text-left font-medium">
                    {flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} className="border-t hover:bg-muted/30 transition-colors">
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">{table.getFilteredRowModel().rows.length} registros</p>
    </div>
  )
}
