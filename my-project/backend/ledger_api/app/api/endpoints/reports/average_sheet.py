from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

from app.api.services.report.concrete_generators import AverageSheetGenerator
from app.api.services.report.report_processing_service import ReportProcessingService

# APIルーターの初期化
router = APIRouter()

# 共通処理サービスのインスタンス
report_service = ReportProcessingService()


@router.post("/")
async def generate_average_sheet(
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
    period_type: Optional[str] = Form(
        None
    ),  # "oneday" | "oneweek" | "onemonth"（任意）
) -> Response:
    """
    工場平均表生成APIエンドポイント

    受入・ヤード・出荷一覧から平均表を自動集計します。

    Args:
            shipment (UploadFile, optional): 出荷データCSVファイル
            yard (UploadFile, optional): ヤードデータCSVファイル
            receive (UploadFile, optional): 受入データCSVファイル

    Returns:
            StreamingResponse: Excel・PDFファイルが含まれたZIPファイル
    """
    # アップロードされたファイルの整理
    files = {k: v for k, v in {"receive": receive}.items() if v is not None}

    # 対象Generatorを直接生成し、共通フローを実行
    generator = AverageSheetGenerator("average_sheet", files)
    if period_type:
        generator.period_type = period_type
    return report_service.run(generator, files)
