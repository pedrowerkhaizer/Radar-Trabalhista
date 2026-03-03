"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  BarChart3,
  LayoutDashboard,
  TrendingUp,
  ShieldCheck,
  Building2,
  Database,
  Code2,
  Settings,
  Search,
  Users,
  RefreshCw,
  Briefcase,
  Factory,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navSections = [
  {
    title: "MONITOR",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Mercado", href: "/dashboard/mercado", icon: TrendingUp },
    ],
  },
  {
    title: "ANÁLISE",
    items: [
      { label: "Demográfico", href: "/dashboard/demografico", icon: Users },
      { label: "Rotatividade", href: "/dashboard/rotatividade", icon: RefreshCw },
      { label: "Ocupações", href: "/dashboard/ocupacoes", icon: Briefcase },
      { label: "Perspectiva Empresa", href: "/dashboard/empresa", icon: Factory },
    ],
  },
  {
    title: "COMPLIANCE",
    items: [
      { label: "Score CNPJ", href: "/dashboard/compliance", icon: ShieldCheck, soon: true },
      { label: "Empresas", href: "/dashboard/empresas", icon: Building2, soon: true },
    ],
  },
  {
    title: "DADOS",
    items: [
      { label: "CAGED", href: "/dashboard/caged", icon: Database },
      { label: "API", href: "/dashboard/api", icon: Code2, soon: true },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-[var(--sidebar-width)] flex-col border-r border-slate-200 bg-white">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-slate-100 px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600">
          <BarChart3 className="h-4 w-4 text-white" />
        </div>
        <span className="text-sm font-semibold text-slate-900">Radar Trabalhista</span>
      </div>

      {/* Search */}
      <div className="px-3 py-3">
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-400">
          <Search className="h-3.5 w-3.5" />
          <span className="flex-1">Pesquisar...</span>
          <kbd className="hidden rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 sm:block">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-6">
        {navSections.map((section) => (
          <div key={section.title}>
            <p className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              {section.title}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(item.href))
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors",
                        isActive
                          ? "bg-blue-50 text-blue-700 font-medium"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      )}
                    >
                      <item.icon
                        className={cn(
                          "h-4 w-4 shrink-0",
                          isActive ? "text-blue-600" : "text-slate-400"
                        )}
                      />
                      <span className="flex-1">{item.label}</span>
                      {item.soon && (
                        <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
                          Em breve
                        </span>
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-100 p-3">
        <div className="flex items-center gap-2.5 rounded-lg px-2 py-2">
          <div className="h-7 w-7 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-[11px] font-bold text-white">
            PW
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-slate-700">Pedro Werkhaizer</p>
            <p className="truncate text-[11px] text-slate-400">Admin</p>
          </div>
          <Settings className="h-4 w-4 shrink-0 text-slate-400 hover:text-slate-600 cursor-pointer" />
        </div>
      </div>
    </aside>
  )
}
