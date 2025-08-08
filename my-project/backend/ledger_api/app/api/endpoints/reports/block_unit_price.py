# backend/app/api/endpoints/reports/block_unit_price.py

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.api.services.report_processing_service import ReportProcessingService

# APIルーターの初期化
router = APIRouter()

# 共通処理サービスのインスタンス
report_service = ReportProcessingService()


@router.post("/")
async def generate_block_unit_price_report(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
) -> StreamingResponse:
    """
    ブロック単価計算レポート生成APIエンドポイント

    出荷、ヤード、受入データからブロック単価を計算し、レポートを生成します。

    Args:
        shipment (UploadFile, optional): 出荷データCSVファイル
        yard (UploadFile, optional): ヤードデータCSVファイル
        receive (UploadFile, optional): 受入データCSVファイル

    Returns:
        StreamingResponse: Excel・PDFファイルが含まれたZIPファイル
    """
    # アップロードされたファイルの整理
    files = {
        k: v
        for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
        if v is not None
    }

    # 共通処理サービスで完全フローを実行
    return report_service.process_complete_flow("block_unit_price", files)
