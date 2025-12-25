from typing import Optional

from app.config.di_providers import get_management_sheet_usecase
from app.core.usecases.reports.generate_management_sheet import (
    GenerateManagementSheetUseCase,
)
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("")
@router.post("/")
async def generate_management_sheet(
    background_tasks: BackgroundTasks,
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(None),
    usecase: GenerateManagementSheetUseCase = Depends(get_management_sheet_usecase),
) -> JSONResponse:
    """
    経営管理表生成APIエンドポイント

    🔄 リファクタリング: Excel同期 + PDF非同期の2段階構成
    - Excel生成は同期的に実行し、すぐにダウンロードURL返却
    - PDF生成はバックグラウンドで実行
    - フロントエンドは pdf_status をポーリングして完了を確認

    Args:
        background_tasks: FastAPIのBackgroundTasks（PDF非同期生成用）
        shipment: 出荷データCSVファイル
        yard: ヤードデータCSVファイル
        receive: 受入データCSVファイル
        period_type: 期間フィルタ ("oneday" | "oneweek" | "onemonth")
        usecase: 依存性注入されたUseCase

    Returns:
        JSONResponse: 署名付きURLを含むレスポンス
            - artifact.excel_download_url: Excelダウンロード用URL（即時利用可能）
            - artifact.report_token: PDFステータス確認用トークン
            - metadata.pdf_status: "pending" | "ready"
    """
    return usecase.execute(
        shipment=shipment,
        yard=yard,
        receive=receive,
        period_type=period_type,
        background_tasks=background_tasks,
        async_pdf=True,
    )
