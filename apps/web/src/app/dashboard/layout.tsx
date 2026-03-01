import { Sidebar } from "@/components/layout/Sidebar"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <div className="pl-[var(--sidebar-width)]">
        <main className="min-h-screen">
          {children}
        </main>
      </div>
    </div>
  )
}
