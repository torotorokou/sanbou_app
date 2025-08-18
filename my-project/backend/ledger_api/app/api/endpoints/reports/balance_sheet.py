# backend/app/api/endpoints/reports/balance_sheet.py

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.api.services.report.concrete_generators import BalanceSheetGenerator
from api.services.report.report_processing_service import ReportProcessingService

# APIルーターの初期化
router = APIRouter()

# 共通処理サービスのインスタンス
report_service = ReportProcessingService()


@router.post("/")
async def generate_balance_sheet(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
) -> StreamingResponse:
    """
    工場搬出入収支表生成APIエンドポイント

    受入・ヤード・出荷一覧から収支表を自動集計します。

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

    # 対象Generatorを直接生成し、共通フローを実行
    generator = BalanceSheetGenerator("balance_sheet", files)
    result = report_service.run(generator, files)
    if not isinstance(result, StreamingResponse):
        raise TypeError("Expected StreamingResponse from report_service.run")
    return result
