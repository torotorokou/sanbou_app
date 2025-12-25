# backend/app/api/endpoints/reports/factory_report.py

from typing import Optional

from app.config.di_providers import get_factory_report_usecase
from app.core.usecases.reports import GenerateFactoryReportUseCase
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import Response

# APIルーターの初期化
router = APIRouter()


@router.post("")
@router.post("/")
async def generate_factory_report(
    background_tasks: BackgroundTasks,
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(
        None
    ),  # "oneday" | "oneweek" | "onemonth"（任意）
    usecase: GenerateFactoryReportUseCase = Depends(get_factory_report_usecase),
) -> Response:
    """
    工場日報生成APIエンドポイント

    ヤードと出荷データから工場内の稼働日報を生成します。

    🔄 リファクタリング: Excel同期 + PDF非同期の2段階構成
    - Excel生成は同期的に実行し、すぐにダウンロードURL返却
    - PDF生成はバックグラウンドで実行
    - フロントエンドは pdf_status をポーリングして完了を確認

    Args:
        background_tasks: FastAPIのBackgroundTasks（PDF非同期生成用）
        shipment (UploadFile, optional): 出荷データCSVファイル
        yard (UploadFile, optional): ヤードデータCSVファイル
        receive (UploadFile, optional): 受入データCSVファイル
        period_type (str, optional): 期間フィルタ ("oneday" | "oneweek" | "onemonth")
        usecase: 工場日報生成 UseCase（DI により注入）

    Returns:
        JSONResponse: 署名付き URL を含むレスポンス
            - artifact.excel_download_url: Excelダウンロード用URL（即時利用可能）
            - artifact.report_token: PDFステータス確認用トークン
            - metadata.pdf_status: "pending" | "ready"
    """
    # アップロードされたファイルの整理
    files = {
        k: v
        for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
        if v is not None
    }

    # UseCase を実行（BackgroundTasksを渡してPDF非同期生成）
    return usecase.execute(
        files=files,
        period_type=period_type,
        background_tasks=background_tasks,
        async_pdf=True,
    )
