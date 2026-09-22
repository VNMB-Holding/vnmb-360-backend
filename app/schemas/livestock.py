from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal

class LivestockInventoryBase(BaseModel):
    upload_id: Optional[int] = None
    unit: Optional[str] = None
    owner: Optional[str] = None
    location_type: Optional[str] = None
    contract_id: Optional[str] = None
    cattle_partner: Optional[str] = None
    head_count: Optional[int] = None
    total_value: Optional[Decimal] = None
    avg_per_head: Optional[Decimal] = None
    total_farm_weight: Optional[Decimal] = None
    total_freight_per_head: Optional[Decimal] = None
    total_commission: Optional[Decimal] = None

class LivestockInventoryCreate(LivestockInventoryBase):
    pass

class LivestockInventoryResponse(LivestockInventoryBase):
    id: int
    upload_id: int
    model_config = ConfigDict(from_attributes=True)

class LivestockLocalDistribution(BaseModel):
    local: str
    cabecas: int
    pct_cabecas: float
    valor: Decimal
    pct_valor: float

class LivestockUFDistribution(BaseModel):
    uf: str
    cabecas: int
    valor: Decimal
    valor_medio: Decimal
    pct_valor: float

class LivestockOperadorDistribution(BaseModel):
    operador: str
    cabecas: int
    valor: Decimal
    valor_medio: Decimal
    pct_valor: float
    filtro: Optional[str] = None

class LivestockSummaryResponse(BaseModel):
    upload_id: Optional[int] = None
    has_consolidated_summary: bool = False
    header_message: Optional[str] = None
    total_cabecas: int
    valor_rebanho: Decimal
    valor_medio_cabeca: Decimal
    peso_medio_cabeca: Optional[Decimal] = None
    frete_total: Decimal
    comissao_total: Decimal
    investimento_total: Decimal
    distribuicao_local: list[LivestockLocalDistribution] = []
    distribuicao_uf: list[LivestockUFDistribution] = []
    distribuicao_operador: list[LivestockOperadorDistribution] = []
