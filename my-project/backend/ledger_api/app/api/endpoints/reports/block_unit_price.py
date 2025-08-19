# backend/app/api/endpoints/reports/block_unit_price.py

from typing import Optional

from api.services.report.report_processing_service import ReportProcessingService
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

from app.api.services.report.concrete_generators import BlockUnitPriceGenerator

# APIルーターの初期化
router = APIRouter()

# 共通処理サービスのインスタンス
report_service = ReportProcessingService()


@router.post("/")
async def generate_block_unit_price_report(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(
        None
    ),  # "oneday" | "oneweek" | "onemonth"（任意）
) -> Response:
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

    # 対象Generatorを直接生成し、共通フローを実行
    generator = BlockUnitPriceGenerator("block_unit_price", files)
    if period_type:
        generator.period_type = period_type
    return report_service.run(generator, files)
