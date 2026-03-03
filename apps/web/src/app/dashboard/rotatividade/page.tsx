import type { Metadata } from "next"
import { RotatividadeContent } from "./RotatividadeContent"

export const metadata: Metadata = { title: "Rotatividade — Radar Trabalhista" }

export default function RotatividadePage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Rotatividade</h1>
        <p className="text-sm text-slate-500 mt-0.5">Análise de causas de desligamento e tempo de emprego</p>
      </div>
      <RotatividadeContent />
    </div>
  )
}
