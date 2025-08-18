# backend/app/api/endpoints/reports/factory_report.py

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.api.services.report.concrete_generators import FactoryReportGenerator
from api.services.report.report_processing_service import ReportProcessingService

# APIルーターの初期化
router = APIRouter()

# 共通処理サービスのインスタンス
report_service = ReportProcessingService()


@router.post("/")
async def generate_factory_report(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
) -> StreamingResponse:
    """
    工場日報生成APIエンドポイント

    ヤードと出荷データから工場内の稼働日報を生成します。

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
    generator = FactoryReportGenerator("factory_report", files)
    return report_service.run(generator, files)
