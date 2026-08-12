from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Optional, List

from app.models import (
    ExcelUploadLog,
    RealEstate,
    VehicleFleet,
    LivestockInventory,
    FinancialInvestment,
    DebtControl
)
from app.schemas.summary import DashboardSummaryResponse, EvolutionPoint

class DashboardService:
    @staticmethod
    def _compute_net_worth_for_upload(db: Session, upload_id: int):
        re_total = db.query(func.coalesce(func.sum(RealEstate.market_value), 0)).filter(
            RealEstate.upload_id == upload_id
        ).scalar()
        re_total = Decimal(str(re_total))

        veh_total = db.query(func.coalesce(func.sum(VehicleFleet.market_value), 0)).filter(
            VehicleFleet.upload_id == upload_id
        ).scalar()
        veh_total = Decimal(str(veh_total))

        # Livestock total including Freight and Commission (as in Relatório Semanal BI formula)
        live_subtotal = db.query(func.coalesce(func.sum(LivestockInventory.total_value), 0)).filter(
            LivestockInventory.upload_id == upload_id
        ).scalar()
        live_freight = db.query(func.coalesce(func.sum(LivestockInventory.total_freight_per_head), 0)).filter(
            LivestockInventory.upload_id == upload_id
        ).scalar()
        live_commission = db.query(func.coalesce(func.sum(LivestockInventory.total_commission), 0)).filter(
            LivestockInventory.upload_id == upload_id
        ).scalar()
        live_total = Decimal(str(live_subtotal)) + Decimal(str(live_freight)) + Decimal(str(live_commission))

        # Investments: use the latest reference_date snapshot (06/2026 = 481.113.840,54)
        latest_inv_date = db.query(func.max(FinancialInvestment.reference_date)).filter(
            FinancialInvestment.upload_id == upload_id
        ).scalar()
        if latest_inv_date:
            inv_total = db.query(func.coalesce(func.sum(FinancialInvestment.amount), 0)).filter(
                FinancialInvestment.upload_id == upload_id,
                FinancialInvestment.reference_date == latest_inv_date,
                ~FinancialInvestment.asset_name.in_(['INVESTIMENTOS', 'CAIXA', 'Offshore (VB AGRO) - BTG'])
            ).scalar()
            inv_total = Decimal(str(inv_total))
        else:
            inv_total = Decimal("0.00")

        # Debts: use reference_date matching latest_inv_date (30/06/2026 = 1.302.503.762,00)
        if latest_inv_date:
            debt_row = db.query(DebtControl).filter(
                DebtControl.upload_id == upload_id,
                DebtControl.reference_date <= latest_inv_date
            ).order_by(DebtControl.reference_date.desc()).first()
            if debt_row and debt_row.final_balance:
                debt_total = abs(Decimal(str(debt_row.final_balance)))
                latest_debt_date = debt_row.reference_date
            else:
                debt_total = Decimal("0.00")
                latest_debt_date = None
        else:
            debt_total = Decimal("0.00")
            latest_debt_date = None

        # Caixa total from FinancialInvestment if stored under 'CAIXA' asset_name
        if latest_inv_date:
            caixa_row = db.query(func.coalesce(func.sum(FinancialInvestment.amount), 0)).filter(
                FinancialInvestment.upload_id == upload_id,
                FinancialInvestment.reference_date == latest_inv_date,
                FinancialInvestment.asset_name == 'CAIXA'
            ).scalar()
            caixa_total = Decimal(str(caixa_row))
        else:
            caixa_total = Decimal("0.00")

        # Exact formula from Relatório Semanal sheet (Line 31):
        # Total Assets = Planilhão (1.302.503.762,00) + Investimentos (337.307.431,48) + Imóveis (1.242.600.000,00) + Estoque Gado (228.652.221,15) + Caixa (131.072.820,92) + Bens Móveis (249.625.499,00)
        # Net Worth = 3.491.761.734,55
        net_worth = debt_total + (inv_total - caixa_total) + re_total + live_total + caixa_total + veh_total
        return {
            "re_total": re_total,
            "veh_total": veh_total,
            "live_total": live_total,
            "inv_total": inv_total,
            "caixa_total": caixa_total,
            "latest_inv_date": latest_inv_date,
            "debt_total": debt_total,
            "latest_debt_date": latest_debt_date,
            "net_worth": net_worth
        }

    @staticmethod
    def get_summary(db: Session, upload_id: Optional[int] = None) -> DashboardSummaryResponse:
        upload_filename = None
        
        all_logs = db.query(ExcelUploadLog).order_by(ExcelUploadLog.id.asc()).all()

        if upload_id is None:
            if all_logs:
                latest_log = all_logs[-1]
                upload_id = latest_log.id
                upload_filename = latest_log.filename
        else:
            log_item = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_id).first()
            if log_item:
                upload_filename = log_item.filename

        # No uploads in DB at all — return all zeros, no mocks
        if upload_id is None:
            return DashboardSummaryResponse(
                upload_id=None,
                upload_filename=None,
                total_real_estate=Decimal("0.00"),
                total_vehicles=Decimal("0.00"),
                total_livestock=Decimal("0.00"),
                total_investments=Decimal("0.00"),
                latest_investment_date=None,
                total_debts=Decimal("0.00"),
                latest_debt_date=None,
                net_worth=Decimal("0.00"),
                weekly_variation_val=Decimal("0.00"),
                weekly_variation_pct=0.0,
                accumulated_variation_val=Decimal("0.00"),
                accumulated_variation_pct=0.0,
                cdi_weekly_pp=0.0,
                cdi_weekly_pct_cdi=0.0,
                cdi_accumulated_pp=0.0,
                cdi_accumulated_pct_cdi=0.0,
                evolution_history=[]
            )

        current_data = DashboardService._compute_net_worth_for_upload(db, upload_id)
        current_nw = current_data["net_worth"]

        # Weekly variation: compare with the immediately previous upload
        prev_log = (
            db.query(ExcelUploadLog)
            .filter(ExcelUploadLog.id < upload_id)
            .order_by(ExcelUploadLog.id.desc())
            .first()
        )
        if prev_log:
            prev_nw = DashboardService._compute_net_worth_for_upload(db, prev_log.id)["net_worth"]
            weekly_var_val = current_nw - prev_nw
            weekly_var_pct = float((weekly_var_val / prev_nw) * 100) if prev_nw > 0 else 0.0
        else:
            weekly_var_val = Decimal("0.00")
            weekly_var_pct = 0.0

        # Accumulated variation: compare with the very first upload
        first_log = all_logs[0] if all_logs else None
        if first_log and first_log.id != upload_id:
            first_nw = DashboardService._compute_net_worth_for_upload(db, first_log.id)["net_worth"]
            accum_var_val = current_nw - first_nw
            accum_var_pct = float((accum_var_val / first_nw) * 100) if first_nw > 0 else 0.0
        else:
            accum_var_val = Decimal("0.00")
            accum_var_pct = 0.0

        # Evolution history: one point per upload log, labelled by filename
        evolution_points: List[EvolutionPoint] = []
        for log in all_logs:
            nw = DashboardService._compute_net_worth_for_upload(db, log.id)["net_worth"]
            val_in_millions = float(nw) / 1_000_000.0
            label = log.filename.split('.')[0][:12] if log.filename else f"Lote {log.id}"
            evolution_points.append(
                EvolutionPoint(
                    semana=label,
                    valor=round(val_in_millions, 2),
                    display_val=f"R$ {float(nw):,.2f}"
                )
            )

        # CDI benchmark: use avg_cdi_percentage from DebtControl if available
        # (FinancialInvestment model has no yield_percentage field)
        avg_cdi = db.query(func.avg(DebtControl.avg_cdi_percentage)).filter(
            DebtControl.upload_id == upload_id
        ).scalar()
        avg_cdi_val = float(avg_cdi) if avg_cdi is not None else 0.0

        return DashboardSummaryResponse(
            upload_id=upload_id,
            upload_filename=upload_filename,
            total_real_estate=current_data["re_total"],
            total_vehicles=current_data["veh_total"],
            total_livestock=current_data["live_total"],
            total_investments=current_data["inv_total"],
            latest_investment_date=current_data["latest_inv_date"],
            total_caixa=current_data["caixa_total"],
            total_debts=current_data["debt_total"],
            latest_debt_date=current_data["latest_debt_date"],
            net_worth=current_nw,
            weekly_variation_val=weekly_var_val,
            weekly_variation_pct=round(weekly_var_pct, 2),
            accumulated_variation_val=accum_var_val,
            accumulated_variation_pct=round(accum_var_pct, 2),
            cdi_weekly_pp=round(avg_cdi_val, 2),
            cdi_weekly_pct_cdi=round(avg_cdi_val, 2),
            cdi_accumulated_pp=round(avg_cdi_val, 2),
            cdi_accumulated_pct_cdi=round(avg_cdi_val, 2),
            evolution_history=evolution_points
        )

    @staticmethod
    def get_history(db: Session) -> List[EvolutionPoint]:
        summary = DashboardService.get_summary(db)
        return summary.evolution_history
