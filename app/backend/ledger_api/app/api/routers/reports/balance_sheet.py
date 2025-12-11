# backend/app/api/endpoints/reports/balance_sheet.py

from typing import Optional

from app.core.usecases.reports.generate_balance_sheet import GenerateBalanceSheetUseCase
from app.config.di_providers import get_balance_sheet_usecase
from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile, Depends
from fastapi.responses import JSONResponse

# APIルーターの初期化
router = APIRouter()


@router.post("")
@router.post("/")
async def generate_balance_sheet(
    background_tasks: BackgroundTasks,
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(None),
    usecase: GenerateBalanceSheetUseCase = Depends(get_balance_sheet_usecase),
) -> JSONResponse:
    """
    工場搬出入収支表生成APIエンドポイント

    受入・ヤード・出荷一覧から収支表を自動集計します。
    
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
