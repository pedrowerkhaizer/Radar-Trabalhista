"use client"
import { MapContainer, TileLayer } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import type { MapaUFProps } from "./MapaUF"

// Mapa simples com cor baseada no saldo
// GeoJSON das UFs será adicionado em implementação futura (PW-44 cont.)
export default function MapaUFInner({ isLoading }: MapaUFProps) {
  if (isLoading) return null // Skeleton já no wrapper

  return (
    <div className="h-80 rounded-lg overflow-hidden border">
      <MapContainer
        center={[-15.7801, -47.9292]}
        zoom={4}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          opacity={0.6}
        />
        {/* GeoJSON das UFs será adicionado na implementação completa (PW-44 cont.) */}
      </MapContainer>
      <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded-sm" aria-hidden="true" />
          <span>Saldo positivo</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-sm" aria-hidden="true" />
          <span>Saldo negativo</span>
        </div>
      </div>
    </div>
  )
}
