"use client"
// MapaUF é carregado dinamicamente para evitar SSR errors com Leaflet
// O componente real está em MapaUFInner.tsx
import dynamic from "next/dynamic"
import { Skeleton } from "@/components/ui/skeleton"
import type { CAGEDMapItem } from "@/lib/types"

export interface MapaUFProps {
  data: CAGEDMapItem[]
  isLoading?: boolean
}

const MapaUFInner = dynamic(() => import("./MapaUFInner"), {
  ssr: false,
  loading: () => <Skeleton className="h-80 w-full rounded-lg" />,
})

export function MapaUF(props: MapaUFProps) {
  return <MapaUFInner {...props} />
}
