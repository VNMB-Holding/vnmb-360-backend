from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.session import get_db
from app.services.excel_parser import ExcelParserService
from app.models import (
    ExcelUploadLog,
    DebtControl,
    FinancialInvestment,
    RealEstate,
    LivestockInventory,
    VehicleFleet
)
from app.schemas.upload_log import ExcelUploadLogResponse

router = APIRouter()

def process_and_persist_excel(filename: str, file_bytes: bytes, db: Session) -> Dict[str, Any]:
    try:
        parsed_data = ExcelParserService.parse_excel(file_bytes)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falha ao ler arquivo Excel: {str(e)}"
        )

    try:
        # Create a new upload log batch entry
        upload_log = ExcelUploadLog(
            filename=filename,
            records_ingested={}
        )
        db.add(upload_log)
        db.flush()  # Generate upload_log.id

        upload_id = upload_log.id
        counts = {}

        # 1. Debt Control
        debts = [DebtControl(upload_id=upload_id, **item) for item in parsed_data.get('debt_control', [])]
        db.bulk_save_objects(debts)
        counts['debt_control'] = len(debts)

        # 2. Financial Investment
        investments = [FinancialInvestment(upload_id=upload_id, **item) for item in parsed_data.get('financial_investment', [])]
        db.bulk_save_objects(investments)
        counts['financial_investment'] = len(investments)

        # 3. Real Estate
        real_estates = [RealEstate(upload_id=upload_id, **item) for item in parsed_data.get('real_estate', [])]
        db.bulk_save_objects(real_estates)
        counts['real_estate'] = len(real_estates)

        # 4. Livestock Inventory
        livestock = [LivestockInventory(upload_id=upload_id, **item) for item in parsed_data.get('livestock_inventory', [])]
        db.bulk_save_objects(livestock)
        counts['livestock_inventory'] = len(livestock)

        # 5. Vehicle Fleet
        vehicles = [VehicleFleet(upload_id=upload_id, **item) for item in parsed_data.get('vehicle_fleet', [])]
        db.bulk_save_objects(vehicles)
        counts['vehicle_fleet'] = len(vehicles)

        upload_log.records_ingested = counts
        upload_log.summary_metrics = parsed_data.get('summary_metrics', {})
        db.commit()

        
        return {
            "message": "Excel file uploaded and data successfully ingested into history batch.",
            "upload_id": upload_id,
            "filename": filename,
            "records_ingested": counts,
            "warnings": parsed_data.get('warnings', [])
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database insertion failed: {str(e)}"
        )

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.xlsm')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido de extensão. Por favor envie um arquivo Excel (.xlsx ou .xls)."
        )
    contents = await file.read()
    return process_and_persist_excel(file.filename, contents, db)

@router.post("/upload-excel", status_code=status.HTTP_201_CREATED)
async def upload_excel_alias(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await upload_excel(file=file, db=db)

@router.get("/uploads", response_model=List[ExcelUploadLogResponse])
def list_upload_history(db: Session = Depends(get_db)):
    return db.query(ExcelUploadLog).order_by(ExcelUploadLog.id.desc()).all()

@router.delete("/upload/{upload_id}", status_code=status.HTTP_200_OK)
def delete_upload_log(upload_id: int, db: Session = Depends(get_db)):
    upload_log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_id).first()
    if not upload_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload log com ID {upload_id} não foi encontrado."
        )
    
    try:
        # Delete the upload log (cascade will handle child table records)
        db.delete(upload_log)
        db.commit()
        return {
            "message": f"Upload #{upload_id} ('{upload_log.filename}') e todos os registros associados foram excluídos com sucesso.",
            "deleted_upload_id": upload_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao excluir o upload #{upload_id}: {str(e)}"
        )
