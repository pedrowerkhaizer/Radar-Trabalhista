import type { Metadata } from "next"
import { OcupacoesContent } from "./OcupacoesContent"

export const metadata: Metadata = { title: "Ocupações — Radar Trabalhista" }

export default function OcupacoesPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Ocupações (CBO)</h1>
        <p className="text-sm text-slate-500 mt-0.5">Ranking de grupos ocupacionais por admissões e salário</p>
      </div>
      <OcupacoesContent />
    </div>
  )
}
