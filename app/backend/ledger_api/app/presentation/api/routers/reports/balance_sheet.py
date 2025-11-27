# backend/app/api/endpoints/reports/balance_sheet.py

from typing import Optional

from app.application.usecases.reports.generate_balance_sheet import GenerateBalanceSheetUseCase
from app.local_config.di_providers import get_balance_sheet_usecase
from fastapi import APIRouter, File, Form, UploadFile, Depends
from fastapi.responses import JSONResponse

# APIルーターの初期化
router = APIRouter()


@router.post("")
@router.post("/")
async def generate_balance_sheet(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(None),
    usecase: GenerateBalanceSheetUseCase = Depends(get_balance_sheet_usecase),
) -> JSONResponse:
    """
    工場搬出入収支表生成APIエンドポイント

    受入・ヤード・出荷一覧から収支表を自動集計します。

    Args:
        shipment: 出荷データCSVファイル
        yard: ヤードデータCSVファイル
        receive: 受入データCSVファイル
        period_type: 期間フィルタ ("oneday" | "oneweek" | "onemonth")
        usecase: 依存性注入されたUseCase

    Returns:
        JSONResponse: 署名付きURLを含むレスポンス
    """
    return usecase.execute(
        shipment=shipment,
        yard=yard,
        receive=receive,
        period_type=period_type,
    )
