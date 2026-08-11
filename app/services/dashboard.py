from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Optional

from app.models import (
    ExcelUploadLog,
    RealEstate,
    VehicleFleet,
    LivestockInventory,
    FinancialInvestment,
    DebtControl
)
from app.schemas.summary import DashboardSummaryResponse

class DashboardService:
    @staticmethod
    def get_summary(db: Session, upload_id: Optional[int] = None) -> DashboardSummaryResponse:
        upload_filename = None
        
        if upload_id is None:
            latest_log = db.query(ExcelUploadLog).order_by(ExcelUploadLog.id.desc()).first()
            if latest_log:
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
                net_worth=Decimal("0.00")
            )

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

        return DashboardSummaryResponse(
            upload_id=upload_id,
            upload_filename=upload_filename,
            total_real_estate=re_total,
            total_vehicles=veh_total,
            total_livestock=live_total,
            total_investments=inv_total,
            latest_investment_date=latest_inv_date,
            total_debts=debt_total,
            latest_debt_date=latest_debt_date,
            net_worth=net_worth
        )
