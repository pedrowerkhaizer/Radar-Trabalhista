import type { Metadata } from "next"
import { DemograficoContent } from "./DemograficoContent"

export const metadata: Metadata = { title: "Perfil Demográfico — Radar Trabalhista" }

export default function DemograficoPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Perfil Demográfico</h1>
        <p className="text-sm text-slate-500 mt-0.5">Distribuição por gênero, idade e escolaridade</p>
      </div>
      <DemograficoContent />
    </div>
  )
}
