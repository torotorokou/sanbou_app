from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, Depends
from fastapi.responses import JSONResponse

from app.core.usecases.reports.generate_management_sheet import GenerateManagementSheetUseCase
from app.config.di_providers import get_management_sheet_usecase

router = APIRouter()


@router.post("")
@router.post("/")
async def generate_management_sheet(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(None),
    usecase: GenerateManagementSheetUseCase = Depends(get_management_sheet_usecase),
) -> JSONResponse:
    """経営管理表生成APIエンドポイント"""
    return await usecase.execute(
        shipment=shipment,
        yard=yard,
        receive=receive,
        period_type=period_type,
    )
