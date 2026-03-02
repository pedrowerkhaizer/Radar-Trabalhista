from typing import Optional

from pydantic import BaseModel, ConfigDict


class CAGEDSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    competencia: str  # "YYYY-MM"
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class CAGEDSummaryResponse(BaseModel):
    data: list[CAGEDSummaryItem]
    total: int
    filtros_aplicados: dict


class CAGEDSeriesResponse(BaseModel):
    series: list[CAGEDSummaryItem]
    meses: int
    cnae2: Optional[str] = None
    uf: Optional[str] = None


class CAGEDMapItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uf: str  # código IBGE 2 dígitos (ex: "35" para SP)
    admissoes: int
    desligamentos: int
    saldo: int
    salario_medio: Optional[float] = None


class CAGEDMapResponse(BaseModel):
    data: list[CAGEDMapItem]
    total: int


class CBOItem(BaseModel):
    cbo6: str
    descricao: str
    admissoes: int = 0
    desligamentos: int = 0
    saldo: int = 0
    salario_medio: Optional[float] = None
