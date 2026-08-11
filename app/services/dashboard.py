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

        live_total = db.query(func.coalesce(func.sum(LivestockInventory.total_value), 0)).filter(
            LivestockInventory.upload_id == upload_id
        ).scalar()
        live_total = Decimal(str(live_total))

        latest_inv_date = db.query(func.max(FinancialInvestment.reference_date)).filter(
            FinancialInvestment.upload_id == upload_id
        ).scalar()
        if latest_inv_date:
            inv_total = db.query(func.coalesce(func.sum(FinancialInvestment.amount), 0)).filter(
                FinancialInvestment.upload_id == upload_id,
                FinancialInvestment.reference_date == latest_inv_date
            ).scalar()
            inv_total = Decimal(str(inv_total))
        else:
            inv_total = Decimal("0.00")

        latest_debt_date = db.query(func.max(DebtControl.reference_date)).filter(
            DebtControl.upload_id == upload_id
        ).scalar()
        if latest_debt_date:
            debt_total = db.query(func.coalesce(func.sum(DebtControl.final_balance), 0)).filter(
                DebtControl.upload_id == upload_id,
                DebtControl.reference_date == latest_debt_date
            ).scalar()
            debt_total = abs(Decimal(str(debt_total)))
        else:
            debt_total = Decimal("0.00")

        net_worth = (re_total + veh_total + live_total + inv_total) - debt_total
        return {
            "re_total": re_total,
            "veh_total": veh_total,
            "live_total": live_total,
            "inv_total": inv_total,
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

        # 100% Real Weekly variation by comparing with previous upload in DB
        prev_log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id < upload_id).order_by(ExcelUploadLog.id.desc()).first()
        if prev_log:
            prev_nw = DashboardService._compute_net_worth_for_upload(db, prev_log.id)["net_worth"]
            weekly_var_val = current_nw - prev_nw
            weekly_var_pct = float((weekly_var_val / prev_nw) * 100) if prev_nw > 0 else 0.0
        else:
            weekly_var_val = Decimal("0.00")
            weekly_var_pct = 0.0

        # 100% Real Accumulated variation by comparing with first upload in DB
        first_log = all_logs[0] if all_logs else None
        if first_log and first_log.id != upload_id:
            first_nw = DashboardService._compute_net_worth_for_upload(db, first_log.id)["net_worth"]
            accum_var_val = current_nw - first_nw
            accum_var_pct = float((accum_var_val / first_nw) * 100) if first_nw > 0 else 0.0
        else:
            accum_var_val = Decimal("0.00")
            accum_var_pct = 0.0

        # 100% Real Evolution history from ExcelUploadLog entries in DB
        evolution_points: List[EvolutionPoint] = []
        for log in all_logs:
            nw = DashboardService._compute_net_worth_for_upload(db, log.id)["net_worth"]
            val_in_millions = float(nw) / 1_000_000.0
            display_name = log.filename.split('.')[0] if log.filename else f"Lote #{log.id}"
            evolution_points.append(
                EvolutionPoint(
                    semana=display_name[:12],
                    valor=round(val_in_millions, 2),
                    display_val=f"R$ {float(nw):,.0f}".replace(',', '.')
                )
            )

        # Compute investment yield average if available
        inv_avg_yield = db.query(func.avg(FinancialInvestment.yield_percentage)).filter(
            FinancialInvestment.upload_id == upload_id
        ).scalar()
        avg_yield = float(inv_avg_yield) if inv_avg_yield is not None else 0.0

        return DashboardSummaryResponse(
            upload_id=upload_id,
            upload_filename=upload_filename,
            total_real_estate=current_data["re_total"],
            total_vehicles=current_data["veh_total"],
            total_livestock=current_data["live_total"],
            total_investments=current_data["inv_total"],
            latest_investment_date=current_data["latest_inv_date"],
            total_debts=current_data["debt_total"],
            latest_debt_date=current_data["latest_debt_date"],
            net_worth=current_nw,
            weekly_variation_val=weekly_var_val,
            weekly_variation_pct=weekly_var_pct,
            accumulated_variation_val=accum_var_val,
            accumulated_variation_pct=accum_var_pct,
            cdi_weekly_pp=round(avg_yield, 2),
            cdi_weekly_pct_cdi=round(avg_yield * 100, 1) if avg_yield else 0.0,
            cdi_accumulated_pp=round(avg_yield, 2),
            cdi_accumulated_pct_cdi=round(avg_yield * 100, 1) if avg_yield else 0.0,
            evolution_history=evolution_points
        )

    @staticmethod
    def get_history(db: Session) -> List[EvolutionPoint]:
        summary = DashboardService.get_summary(db)
        return summary.evolution_history
