# apps/api/schemas/analytics.py
from typing import Optional
from pydantic import BaseModel, ConfigDict


class GeneroItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    competencia: str
    sexo: str
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class GeneroResponse(BaseModel):
    data: list[GeneroItem]
    total: int


class EscolaridadeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    grau_instrucao: int
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class EscolaridadeResponse(BaseModel):
    data: list[EscolaridadeItem]


class FaixaEtariaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    faixa_etaria: str
    admissoes: int
    desligamentos: int
    saldo: int


class FaixaEtariaResponse(BaseModel):
    data: list[FaixaEtariaItem]


class CausaDesligamentoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    causa_desligamento: int
    desligamentos: int
    salario_medio: Optional[float] = None


class CausaDesligamentoResponse(BaseModel):
    data: list[CausaDesligamentoItem]


class TempoEmpregoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    faixa_tempo_emprego: str
    desligamentos: int


class TempoEmpregoResponse(BaseModel):
    data: list[TempoEmpregoItem]


class TipoVinculoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tipo_vinculo: int
    admissoes: int
    desligamentos: int
    saldo: int


class TipoVinculoResponse(BaseModel):
    data: list[TipoVinculoItem]


class PorteEmpresaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    porte_empresa: int
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class PorteEmpresaResponse(BaseModel):
    data: list[PorteEmpresaItem]


class OcupacaoRankingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cbo_grupo: str  # first 2 digits of cbo6
    descricao: Optional[str] = None
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class OcupacaoRankingResponse(BaseModel):
    data: list[OcupacaoRankingItem]
    total: int
