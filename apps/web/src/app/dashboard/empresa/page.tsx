import type { Metadata } from "next"
import { EmpresaContent } from "./EmpresaContent"

export const metadata: Metadata = { title: "Perspectiva Empresa — Radar Trabalhista" }

export default function EmpresaPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-slate-900">Perspectiva Empresa</h1>
        <p className="text-sm text-slate-500 mt-0.5">Admissões e demissões por porte e tipo de vínculo</p>
      </div>
      <EmpresaContent />
    </div>
  )
}
