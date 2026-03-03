export interface CAGEDSummaryItem {
  competencia: string // "YYYY-MM"
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface CAGEDSummaryResponse {
  data: CAGEDSummaryItem[]
  total: number
  filtros_aplicados: Record<string, string>
}

export interface CAGEDSeriesResponse {
  series: CAGEDSummaryItem[]
  meses: number
  cnae2: string | null
  uf: string | null
}

export interface CAGEDMapItem {
  uf: string  // código IBGE 2 dígitos (ex: "35" para SP)
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface CAGEDMapResponse {
  data: CAGEDMapItem[]
  total: number
}

export interface CBOItem {
  cbo6: string
  descricao: string
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface FilterState {
  cnae2?: string
  uf?: string
  periodo_inicio?: string
  periodo_fim?: string
  meses: number
}

export const CNAE_OPTIONS = [
  { value: "01", label: "Agricultura e Pecuária" },
  { value: "10", label: "Indústria de Alimentos" },
  { value: "41", label: "Construção Civil" },
  { value: "45", label: "Comércio de Veículos" },
  { value: "47", label: "Comércio Varejista" },
  { value: "49", label: "Transporte Terrestre" },
  { value: "55", label: "Hospedagem" },
  { value: "56", label: "Alimentação" },
  { value: "62", label: "Tecnologia da Informação" },
  { value: "63", label: "Serviços de Informação" },
  { value: "64", label: "Serviços Financeiros" },
  { value: "70", label: "Gestão Empresarial" },
  { value: "72", label: "Pesquisa e Desenvolvimento" },
  { value: "75", label: "Veterinária" },
  { value: "78", label: "Agências de Emprego" },
  { value: "84", label: "Administração Pública" },
  { value: "85", label: "Educação" },
  { value: "86", label: "Saúde" },
  { value: "88", label: "Assistência Social" },
  { value: "96", label: "Outros Serviços" },
] as const

export const UF_OPTIONS = [
  { value: "AC", label: "Acre" }, { value: "AL", label: "Alagoas" },
  { value: "AM", label: "Amazonas" }, { value: "AP", label: "Amapá" },
  { value: "BA", label: "Bahia" }, { value: "CE", label: "Ceará" },
  { value: "DF", label: "Distrito Federal" }, { value: "ES", label: "Espírito Santo" },
  { value: "GO", label: "Goiás" }, { value: "MA", label: "Maranhão" },
  { value: "MG", label: "Minas Gerais" }, { value: "MS", label: "Mato Grosso do Sul" },
  { value: "MT", label: "Mato Grosso" }, { value: "PA", label: "Pará" },
  { value: "PB", label: "Paraíba" }, { value: "PE", label: "Pernambuco" },
  { value: "PI", label: "Piauí" }, { value: "PR", label: "Paraná" },
  { value: "RJ", label: "Rio de Janeiro" }, { value: "RN", label: "Rio Grande do Norte" },
  { value: "RO", label: "Rondônia" }, { value: "RR", label: "Roraima" },
  { value: "RS", label: "Rio Grande do Sul" }, { value: "SC", label: "Santa Catarina" },
  { value: "SE", label: "Sergipe" }, { value: "SP", label: "São Paulo" },
  { value: "TO", label: "Tocantins" },
] as const

// ── Analytics types ───────────────────────────────────────────────────────────

export interface GeneroItem {
  competencia: string
  sexo: string  // "1"=M, "3"=F
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface EscolaridadeItem {
  grau_instrucao: number
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface FaixaEtariaItem {
  faixa_etaria: string
  admissoes: number
  desligamentos: number
  saldo: number
}

export interface CausaDesligamentoItem {
  causa_desligamento: number
  desligamentos: number
  salario_medio: number | null
}

export interface TempoEmpregoItem {
  faixa_tempo_emprego: string
  desligamentos: number
}

export interface TipoVinculoItem {
  tipo_vinculo: number
  admissoes: number
  desligamentos: number
  saldo: number
}

export interface PorteEmpresaItem {
  porte_empresa: number
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

export interface OcupacaoItem {
  cbo_grupo: string
  descricao: string | null
  admissoes: number
  desligamentos: number
  saldo: number
  salario_medio: number | null
}

// Labels for coded fields
export const SEXO_LABELS: Record<string, string> = {
  "1": "Masculino", "3": "Feminino", "9": "Ignorado",
}

export const GRAU_INSTRUCAO_LABELS: Record<number, string> = {
  1: "Analfabeto", 2: "Fundamental incompleto", 3: "Fundamental completo",
  4: "Médio incompleto", 5: "Médio completo", 6: "Superior incompleto",
  7: "Superior completo", 8: "Mestrado", 9: "Doutorado",
}

export const CAUSA_DESLIG_LABELS: Record<number, string> = {
  11: "Sem justa causa", 12: "Com justa causa", 21: "A pedido",
  22: "Aposentadoria", 23: "Transferência", 31: "Término contrato",
  40: "Falecimento", 99: "Outros",
}

export const PORTE_LABELS: Record<number, string> = {
  1: "1–10", 2: "11–50", 3: "51–200", 4: "201–500", 5: "501–1000", 6: "1001+",
}

export const TIPO_VINCULO_LABELS: Record<number, string> = {
  10: "CLT", 15: "CLT doméstico", 20: "Estatutário", 25: "Temporário",
  30: "Avulso", 35: "Aprendiz", 40: "Menor aprendiz", 55: "Outros",
}
