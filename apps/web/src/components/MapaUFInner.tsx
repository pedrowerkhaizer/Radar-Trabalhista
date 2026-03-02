"use client"
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import { useState, useEffect } from "react"
import type { FeatureCollection } from "geojson"
import type { MapaUFProps } from "./MapaUF"

// GeoJSON das UFs brasileiras (fonte: IBGE servicodados API v3)
// features.properties.codarea = código IBGE 2 dígitos (ex: "35" para SP)
const IBGE_STATES_URL =
  "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR" +
  "?formato=application/vnd.geo+json&qualidade=minima&divisao=UF"

function getSaldoColor(saldo: number, maxAbs: number): string {
  if (maxAbs === 0 || saldo === 0) return "#e2e8f0"
  const intensity = Math.min(Math.abs(saldo) / maxAbs, 1)
  if (saldo > 0) {
    // Verde: intensidade de claro (#bbf7d0) a escuro (#15803d)
    const r = Math.round(187 - 172 * intensity)
    const g = Math.round(247 - 119 * intensity)
    const b = Math.round(208 - 147 * intensity)
    return `rgb(${r}, ${g}, ${b})`
  }
  // Vermelho: intensidade de claro (#fecaca) a escuro (#b91c1c)
  const r = Math.round(254 - 69 * intensity)
  const g = Math.round(202 - 174 * intensity)
  const b = Math.round(202 - 174 * intensity)
  return `rgb(${r}, ${g}, ${b})`
}

export default function MapaUFInner({ data, isLoading }: MapaUFProps) {
  const [geoJSON, setGeoJSON] = useState<FeatureCollection | null>(null)

  useEffect(() => {
    fetch(IBGE_STATES_URL)
      .then((res) => res.json())
      .then(setGeoJSON)
      .catch(() => {
        // GeoJSON não disponível — mapa ainda funciona sem coroplético
      })
  }, [])

  // Mapeia código UF (IBGE) → saldo e calcula o máximo absoluto para a escala de cores
  const saldoByUF: Record<string, number> = {}
  let maxAbs = 0
  for (const item of data) {
    saldoByUF[item.uf] = item.saldo
    if (Math.abs(item.saldo) > maxAbs) maxAbs = Math.abs(item.saldo)
  }

  // Serialização do mapa de saldo como key força re-render do GeoJSON quando os dados mudam
  const geoJSONKey = JSON.stringify(saldoByUF)

  if (isLoading) return null

  return (
    <div>
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
            opacity={0.35}
          />
          {geoJSON && (
            <GeoJSON
              key={geoJSONKey}
              data={geoJSON}
              style={(feature) => ({
                fillColor: getSaldoColor(
                  saldoByUF[feature?.properties?.codarea as string] ?? 0,
                  maxAbs
                ),
                weight: 1,
                opacity: 1,
                color: "#64748b",
                fillOpacity: 0.8,
              })}
            />
          )}
        </MapContainer>
      </div>
      <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded-sm" aria-hidden="true" />
          <span>Saldo positivo</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-slate-200 rounded-sm" aria-hidden="true" />
          <span>Neutro / sem dados</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-sm" aria-hidden="true" />
          <span>Saldo negativo</span>
        </div>
      </div>
    </div>
  )
}
