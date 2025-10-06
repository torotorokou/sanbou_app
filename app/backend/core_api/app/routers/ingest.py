"""
Ingest router: CSV upload and reservation endpoints.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.infra.db import get_db
from app.services.ingest_service import IngestService
from app.domain.models import ReservationCreate, ReservationResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/csv", summary="Upload CSV data")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload CSV file with inbound actuals.
    TODO: Define CSV column spec.
    Expected columns: date, trucks, weight, vendor, etc.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # TODO: Validate required columns
        # TODO: Parse and normalize data (e.g., date formats, numeric types)
        rows = df.to_dict(orient="records")

        service = IngestService(db)
        result = service.upload_csv(rows)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@router.post("/reserve", response_model=ReservationResponse, summary="Create truck reservation")
def create_reservation(
    req: ReservationCreate,
    db: Session = Depends(get_db),
):
    """
    Create or update a truck reservation for a specific date.
    """
    service = IngestService(db)
    return service.create_reservation(req)
