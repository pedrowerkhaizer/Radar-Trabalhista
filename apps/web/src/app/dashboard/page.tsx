import { Suspense } from "react"
import { DashboardContent } from "./DashboardContent"
import { DashboardSkeleton } from "./loading"

export default function DashboardPage() {
  return (
    <>
      {/* Page header */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span>Radar Trabalhista</span>
              <span>/</span>
              <span className="text-slate-700 font-medium">Monitor CAGED</span>
            </div>
            <h1 className="mt-0.5 text-xl font-semibold text-slate-900">
              Monitor de Mercado
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 bg-slate-100 px-2.5 py-1.5 rounded-lg">
              Dados CAGED · Atualizado mensalmente
            </span>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        <Suspense fallback={<DashboardSkeleton />}>
          <DashboardContent />
        </Suspense>
      </div>
    </>
  )
}
