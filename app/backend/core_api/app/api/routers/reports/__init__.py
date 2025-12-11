"""
Reports Router - BFF for ledger_api report endpoints
フロントエンドからの全レポートリクエストを受け、ledger_apiに転送

このモジュールは複数のサブモジュールに分割されています:
- factory_report.py: 工場日報生成
- balance_sheet.py: 収支表生成  
- average_sheet.py: 平均表生成
- management_sheet.py: 管理表生成
- artifacts.py: レポートアーティファクト(Excel/PDF)のストリーミングプロキシ
- jobs.py: ジョブステータス取得・通知ストリーム

設計方針:
  - 各エンドポイントを独立したファイルに分離（単一責任原則）
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - ExternalServiceError で外部サービスエラーをラップ
"""
from fastapi import APIRouter

# サブルーターをインポート
from .factory_report import router as factory_report_router
from .balance_sheet import router as balance_sheet_router
from .average_sheet import router as average_sheet_router
from .management_sheet import router as management_sheet_router
from .artifacts import router as artifacts_router
from .jobs import router as jobs_router
from .pdf_status import router as pdf_status_router

# メインルーター
router = APIRouter(prefix="/reports", tags=["reports"])

# サブルーターを統合
router.include_router(factory_report_router)
router.include_router(balance_sheet_router)
router.include_router(average_sheet_router)
router.include_router(management_sheet_router)
router.include_router(artifacts_router)
router.include_router(jobs_router)
router.include_router(pdf_status_router)
