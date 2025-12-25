"""
Database Router - CSV upload and database operations
フロントエンドからのCSVアップロードを受け、DBに保存

このモジュールは複数のサブモジュールに分割されています:
- upload.py: 将軍CSV3種類のアップロードエンドポイント
- upload_status.py: アップロード処理ステータス照会
- upload_calendar.py: アップロードカレンダー取得・削除

設計方針:
  - Router層は HTTP I/O と DI の入口のみ
  - ビジネスロジックは UseCase に委譲
  - DI は config/di_providers.py に集約
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - ValidationError でバリデーションエラーを表現
  - InfrastructureError でDB操作エラーを表現
  - NotFoundError でリソース不存在を表現

Note:
  - 旧router.pyにあったDEPRECATEDなcache/clearエンドポイントは削除されました
  - UseCaseパターンではTTLキャッシュを使用せず常に最新データを取得します
"""

from fastapi import APIRouter

# サブルーターをインポート
from .upload import router as upload_router
from .upload_calendar import router as upload_calendar_router
from .upload_status import router as upload_status_router

# メインルーター
router = APIRouter(prefix="/database", tags=["database"])

# サブルーターを統合
router.include_router(upload_router)
router.include_router(upload_status_router)
router.include_router(upload_calendar_router)
