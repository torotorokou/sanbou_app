"""
Sales Tree Router - 売上ツリー分析APIエンドポイント

売上ツリー画面で表示するサマリーデータと日次推移データを提供

このモジュールは複数のサブモジュールに分割されています:
- query.py: サマリー、日次推移、Pivotデータ取得
- export.py: CSV出力
- master.py: 営業・顧客・品目フィルタ候補取得
- detail.py: 詳細明細行取得

設計方針:
  - RouterはHTTP I/Oのみを担当（ビジネスロジックはUseCaseに委譲）
  - DI経由でUseCaseを取得（テスタビリティ向上）
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - InfrastructureError でDB操作エラーを表現
"""
from fastapi import APIRouter

# サブルーターをインポート
from .query import router as query_router
from .export import router as export_router
from .master import router as master_router
from .detail import router as detail_router

# メインルーター
router = APIRouter(prefix="/analytics/sales-tree", tags=["sales-tree"])

# サブルーターを統合
router.include_router(query_router)
router.include_router(export_router)
router.include_router(master_router)
router.include_router(detail_router)
