import { Skeleton } from "@/components/ui/skeleton"

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-9 w-32 rounded-lg" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-slate-200 bg-white p-5">
            <Skeleton className="h-3.5 w-20 mb-3" />
            <Skeleton className="h-8 w-28 mb-1.5" />
            <Skeleton className="h-3 w-16 mb-4" />
            <Skeleton className="h-12 w-full" />
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <Skeleton className="h-4 w-32 mb-1" />
        <Skeleton className="h-3 w-48 mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <Skeleton className="h-4 w-32 mb-4" />
          <Skeleton className="h-64 w-full" />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <Skeleton className="h-4 w-32 mb-4" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    </div>
  )
}

export default function DashboardLoading() {
  return (
    <div className="p-6">
      <DashboardSkeleton />
    </div>
  )
}
