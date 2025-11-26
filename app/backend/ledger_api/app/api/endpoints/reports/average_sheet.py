from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, Depends
from fastapi.responses import JSONResponse

from app.core.usecases.reports.generate_average_sheet import GenerateAverageSheetUseCase
from app.config.di_providers import get_average_sheet_usecase

router = APIRouter()


@router.post("")
@router.post("/")
async def generate_average_sheet(
    receive: UploadFile = File(None),
    report_key: Optional[str] = Form(None),
    period_type: Optional[str] = Form(None),
    usecase: GenerateAverageSheetUseCase = Depends(get_average_sheet_usecase),
) -> JSONResponse:
    """
    工場平均表生成APIエンドポイント

    受入一覧から平均表を自動集計します。

    Args:
        receive: 受入データCSVファイル
        report_key: レポートキー（互換性のため）
        period_type: 期間フィルタ
        usecase: 依存性注入されたUseCase

    Returns:
        JSONResponse: 署名付きURLを含むレスポンス
    """
    return usecase.execute(
        receive=receive,
        period_type=period_type,
    )
