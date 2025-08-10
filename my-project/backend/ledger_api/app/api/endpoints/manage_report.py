"""
帳票管理APIエンドポイント (レガシー)

⚠️ このエンドポイントは旧バージョンとの互換性のために残されています。
新しい実装では /reports/{report_type}/ エンドポイントをご使用ください。

CSVファイルのアップロード、バリデーション、フォーマット変換、
帳票生成、Excel・PDF出力、ZIP圧縮までの一連の処理を行うAPIエンドポイントです。
"""

from fastapi import APIRouter, File, Form, UploadFile

from app.api.services.report.generator_factory import get_generator
from api.services.report.report_processing_service import ReportProcessingService

# APIルーターの初期化
router = APIRouter()

# 共通処理サービスのインスタンス
report_service = ReportProcessingService()


@router.post("/report/manage")
async def generate_pdf(
    report_key: str = Form(...),
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
):
    """
    帳票生成APIエンドポイント (レガシー)

    ⚠️ このエンドポイントは旧バージョンとの互換性のために残されています。
    新しい実装では以下のエンドポイントをご使用ください：
    - 工場日報: POST /reports/factory_report/
    - 収支表: POST /reports/balance_sheet/
    - ブロック単価: POST /reports/block_unit_price/

    Args:
        report_key (str): 帳票タイプを識別するキー
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

    # レジストリからGeneratorクラスを取得し、直接実行
    GeneratorCls = get_generator(report_key)
    generator = GeneratorCls(report_key, files)
    return report_service.run(generator, files)
