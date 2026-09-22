from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from decimal import Decimal
import re

from app.db.session import get_db
from app.models import LivestockInventory, ExcelUploadLog
from app.schemas.livestock import (
    LivestockInventoryResponse,
    LivestockSummaryResponse,
    LivestockLocalDistribution,
    LivestockUFDistribution,
    LivestockOperadorDistribution
)

router = APIRouter()

@router.get("/livestock", response_model=List[LivestockInventoryResponse])
def get_livestock(
    upload_id: Optional[int] = Query(None, description="Filter livestock by spreadsheet upload_id (defaults to latest upload if not provided)"),
    db: Session = Depends(get_db)
):
    if upload_id is None:
        upload_id = db.query(func.max(ExcelUploadLog.id)).scalar()
        if upload_id is None:
            return []

    query = db.query(LivestockInventory).filter(LivestockInventory.upload_id == upload_id)

    return query.order_by(LivestockInventory.id.asc()).all()

@router.get("/livestock/summary", response_model=LivestockSummaryResponse)
def get_livestock_summary(
    upload_id: Optional[int] = Query(None, description="Filter livestock summary by spreadsheet upload_id (defaults to latest upload)"),
    db: Session = Depends(get_db)
):
    if upload_id is None:
        upload_id = db.query(func.max(ExcelUploadLog.id)).scalar()
        if upload_id is None:
            return LivestockSummaryResponse(
                upload_id=None,
                has_consolidated_summary=False,
                total_cabecas=0,
                valor_rebanho=Decimal("0.00"),
                valor_medio_cabeca=Decimal("0.00"),
                peso_medio_cabeca=None,
                frete_total=Decimal("0.00"),
                comissao_total=Decimal("0.00"),
                investimento_total=Decimal("0.00"),
                distribuicao_local=[],
                distribuicao_uf=[],
                distribuicao_operador=[]
            )

    log_entry = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_id).first()
    summary_metrics = (log_entry.summary_metrics or {}) if log_entry else {}
    live_meta = summary_metrics.get("livestock")

    if live_meta and live_meta.get("has_consolidated_summary"):
        return LivestockSummaryResponse(
            upload_id=upload_id,
            has_consolidated_summary=True,
            header_message=live_meta.get("header_message"),
            total_cabecas=int(live_meta.get("total_cabecas") or 0),
            valor_rebanho=Decimal(str(round(live_meta.get("valor_rebanho") or 0, 2))),
            valor_medio_cabeca=Decimal(str(round(live_meta.get("valor_medio_cabeca") or 0, 2))),
            peso_medio_cabeca=Decimal(str(round(live_meta.get("peso_medio_cabeca") or 0, 2))) if live_meta.get("peso_medio_cabeca") is not None else None,
            frete_total=Decimal(str(round(live_meta.get("frete_total") or 0, 2))),
            comissao_total=Decimal(str(round(live_meta.get("comissao_total") or 0, 2))),
            investimento_total=Decimal(str(round(live_meta.get("investimento_total") or 0, 2))),
            distribuicao_local=[
                LivestockLocalDistribution(
                    local=item["local"],
                    cabecas=int(item["cabecas"]),
                    pct_cabecas=float(item.get("pct_cabecas", 0)),
                    valor=Decimal(str(round(item["valor"], 2))),
                    pct_valor=float(item.get("pct_valor", 0))
                ) for item in live_meta.get("distribuicao_local", [])
            ],
            distribuicao_uf=[
                LivestockUFDistribution(
                    uf=item["uf"],
                    cabecas=int(item["cabecas"]),
                    valor=Decimal(str(round(item["valor"], 2))),
                    valor_medio=Decimal(str(round(item.get("valor_medio") or 0, 2))),
                    pct_valor=float(item.get("pct_valor", 0))
                ) for item in live_meta.get("distribuicao_uf", [])
            ],
            distribuicao_operador=[
                LivestockOperadorDistribution(
                    operador=item["operador"],
                    cabecas=int(item["cabecas"]),
                    valor=Decimal(str(round(item["valor"], 2))),
                    valor_medio=Decimal(str(round(item.get("valor_medio") or 0, 2))),
                    pct_valor=float(item.get("pct_valor", 0)),
                    filtro=item.get("filtro")
                ) for item in live_meta.get("distribuicao_operador", [])
            ]
        )

    items = db.query(LivestockInventory).filter(LivestockInventory.upload_id == upload_id).all()
    if not items:
        return LivestockSummaryResponse(
            upload_id=upload_id,
            has_consolidated_summary=False,
            total_cabecas=0,
            valor_rebanho=Decimal("0.00"),
            valor_medio_cabeca=Decimal("0.00"),
            peso_medio_cabeca=None,
            frete_total=Decimal("0.00"),
            comissao_total=Decimal("0.00"),
            investimento_total=Decimal("0.00"),
            distribuicao_local=[],
            distribuicao_uf=[],
            distribuicao_operador=[]
        )

    tot_cab = sum(r.head_count or 0 for r in items)
    tot_val = sum(Decimal(str(r.total_value or 0)) for r in items)
    tot_frete = sum(Decimal(str(r.total_freight_per_head or 0)) for r in items)
    tot_comm = sum(Decimal(str(r.total_commission or 0)) for r in items)
    tot_invest = tot_val + tot_frete + tot_comm
    v_med = (tot_val / tot_cab) if tot_cab > 0 else Decimal("0.00")

    tot_weight_pts = sum(float(r.total_farm_weight or 0) * (r.head_count or 0) for r in items if r.total_farm_weight)
    p_med = Decimal(str(round(tot_weight_pts / tot_cab, 2))) if tot_cab > 0 and tot_weight_pts > 0 else None

    loc_map = {}
    for r in items:
        loc = r.location_type or "Outros"
        if loc not in loc_map:
            loc_map[loc] = {"cab": 0, "val": Decimal("0.00")}
        loc_map[loc]["cab"] += (r.head_count or 0)
        loc_map[loc]["val"] += Decimal(str(r.total_value or 0))

    dist_local = [
        LivestockLocalDistribution(
            local=k,
            cabecas=v["cab"],
            pct_cabecas=(v["cab"] / tot_cab) if tot_cab > 0 else 0.0,
            valor=v["val"],
            pct_valor=float(v["val"] / tot_val) if tot_val > 0 else 0.0
        ) for k, v in loc_map.items()
    ]

    uf_map = {}
    for r in items:
        text = f"{r.unit or ''} {r.cattle_partner or ''}".upper()
        found_uf = "MT"
        for uf in ['MT', 'SP', 'MS', 'GO', 'MG', 'BA', 'PR', 'PA', 'RO', 'TO']:
            if re.search(rf"\b{uf}\b|\({uf}\)|-{uf}", text):
                found_uf = uf
                break
        if found_uf not in uf_map:
            uf_map[found_uf] = {"cab": 0, "val": Decimal("0.00")}
        uf_map[found_uf]["cab"] += (r.head_count or 0)
        uf_map[found_uf]["val"] += Decimal(str(r.total_value or 0))

    dist_uf = [
        LivestockUFDistribution(
            uf=k,
            cabecas=v["cab"],
            valor=v["val"],
            valor_medio=(v["val"] / v["cab"]) if v["cab"] > 0 else Decimal("0.00"),
            pct_valor=float(v["val"] / tot_val) if tot_val > 0 else 0.0
        ) for k, v in uf_map.items()
    ]

    op_map = {}
    for r in items:
        op = r.cattle_partner or r.unit or "Outros"
        if op not in op_map:
            op_map[op] = {"cab": 0, "val": Decimal("0.00")}
        op_map[op]["cab"] += (r.head_count or 0)
        op_map[op]["val"] += Decimal(str(r.total_value or 0))

    dist_op = [
        LivestockOperadorDistribution(
            operador=k,
            cabecas=v["cab"],
            valor=v["val"],
            valor_medio=(v["val"] / v["cab"]) if v["cab"] > 0 else Decimal("0.00"),
            pct_valor=float(v["val"] / tot_val) if tot_val > 0 else 0.0,
            filtro=k
        ) for k, v in op_map.items()
    ]

    return LivestockSummaryResponse(
        upload_id=upload_id,
        has_consolidated_summary=False,
        total_cabecas=tot_cab,
        valor_rebanho=round(tot_val, 2),
        valor_medio_cabeca=round(v_med, 2),
        peso_medio_cabeca=p_med,
        frete_total=round(tot_frete, 2),
        comissao_total=round(tot_comm, 2),
        investimento_total=round(tot_invest, 2),
        distribuicao_local=dist_local,
        distribuicao_uf=dist_uf,
        distribuicao_operador=dist_op
    )
