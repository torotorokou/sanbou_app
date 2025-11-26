# backend/app/api/endpoints/reports/factory_report.py

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from app.config.di_providers import get_factory_report_usecase
from app.core.usecases.reports import GenerateFactoryReportUseCase

# APIルーターの初期化
router = APIRouter()


@router.post("")
@router.post("/")
async def generate_factory_report(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(None),  # "oneday" | "oneweek" | "onemonth"（任意）
    usecase: GenerateFactoryReportUseCase = Depends(get_factory_report_usecase),
) -> Response:
    """
    工場日報生成APIエンドポイント

    ヤードと出荷データから工場内の稼働日報を生成します。

    Args:
        shipment (UploadFile, optional): 出荷データCSVファイル
        yard (UploadFile, optional): ヤードデータCSVファイル
        receive (UploadFile, optional): 受入データCSVファイル
        period_type (str, optional): 期間フィルタ ("oneday" | "oneweek" | "onemonth")
        usecase: 工場日報生成 UseCase（DI により注入）

    Returns:
        JSONResponse: 署名付き URL を含むレスポンス
    """
    # アップロードされたファイルの整理
    files = {
        k: v
        for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
        if v is not None
    }

    # UseCase を実行
    return usecase.execute(files=files, period_type=period_type)
