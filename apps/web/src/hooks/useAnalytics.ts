// apps/web/src/hooks/useAnalytics.ts
"use client"
import { useQuery } from "@tanstack/react-query"
import type { FilterState } from "@/lib/types"
import {
  fetchDemograficoGenero, fetchDemograficoEscolaridade, fetchDemograficoFaixaEtaria,
  fetchRotatividadeCausas, fetchRotatividadeTempoEmprego, fetchRotatividadeTipoVinculo,
  fetchOcupacoesRanking, fetchOcupacoesSalario,
  fetchEmpresaPorte, fetchEmpresaTipoVinculo,
} from "@/lib/api-client"

const STALE = 30 * 60 * 1000

function q<T>(key: unknown[], fn: () => Promise<T>) {
  return { queryKey: key, queryFn: fn, staleTime: STALE, retry: 2 } as const
}

export const useDemograficoGenero = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "genero", f], () => fetchDemograficoGenero(f)))

export const useDemograficoEscolaridade = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "escolaridade", f], () => fetchDemograficoEscolaridade(f)))

export const useDemograficoFaixaEtaria = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "faixa_etaria", f], () => fetchDemograficoFaixaEtaria(f)))

export const useRotatividadeCausas = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "causas", f], () => fetchRotatividadeCausas(f)))

export const useRotatividadeTempoEmprego = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "tempo_emprego", f], () => fetchRotatividadeTempoEmprego(f)))

export const useRotatividadeTipoVinculo = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "vinculo_rotat", f], () => fetchRotatividadeTipoVinculo(f)))

export const useOcupacoesRanking = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "ocup_ranking", f], () => fetchOcupacoesRanking(f)))

export const useOcupacoesSalario = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "ocup_salario", f], () => fetchOcupacoesSalario(f)))

export const useEmpresaPorte = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "porte", f], () => fetchEmpresaPorte(f)))

export const useEmpresaTipoVinculo = (f: Partial<FilterState>) =>
  useQuery(q(["analytics", "vinculo_empresa", f], () => fetchEmpresaTipoVinculo(f)))
