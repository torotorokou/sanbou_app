from typing import Optional

from app.config.di_providers import get_average_sheet_usecase
from app.core.usecases.reports.generate_average_sheet import GenerateAverageSheetUseCase
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("")
@router.post("/")
async def generate_average_sheet(
    background_tasks: BackgroundTasks,
    receive: UploadFile = File(None),
    report_key: Optional[str] = Form(None),
    period_type: Optional[str] = Form(None),
    usecase: GenerateAverageSheetUseCase = Depends(get_average_sheet_usecase),
) -> JSONResponse:
    """
    工場平均表生成APIエンドポイント

    受入一覧から平均表を自動集計します。

    🔄 リファクタリング: Excel同期 + PDF非同期の2段階構成
    - Excel生成は同期的に実行し、すぐにダウンロードURL返却
    - PDF生成はバックグラウンドで実行
    - フロントエンドは pdf_status をポーリングして完了を確認

    Args:
        background_tasks: FastAPIのBackgroundTasks（PDF非同期生成用）
        receive: 受入データCSVファイル
        report_key: レポートキー（互換性のため）
        period_type: 期間フィルタ
        usecase: 依存性注入されたUseCase

    Returns:
        JSONResponse: 署名付きURLを含むレスポンス
            - artifact.excel_download_url: Excelダウンロード用URL（即時利用可能）
            - artifact.report_token: PDFステータス確認用トークン
            - metadata.pdf_status: "pending" | "ready"
    """
    return usecase.execute(
        receive=receive,
        period_type=period_type,
        background_tasks=background_tasks,
        async_pdf=True,
    )
