"""
Core API - BFF/Facade for frontend

フロントエンドからのリクエストを受け付け、各マイクロサービスへの処理を振り分けるBFF層。
短い同期呼び出しと、長時間実行タスクのジョブキューイングを担当。

主な責務:
  - フロントエンドからのHTTPリクエストを受け付け
  - 各種マイクロサービス(ledger_api, rag_api等)へのプロキシ
  - 長時間実行タスク(予測ジョブ等)のキューイング
  - CSV アップロード処理
  - ダッシュボード用データの集約

アーキテクチャ:
  - Clean Architecture を採用
  - Domain層: ビジネスロジック、エンティティ、ポート定義
  - Application層: ユースケース(ビジネスフロー)
  - Infrastructure層: データベース、外部API呼び出し
  - Presentation層: HTTPエンドポイント、リクエスト/レスポンス変換
"""
import logging
from fastapi import FastAPI

# ==========================================
# 統一ロギング設定のインポート（backend_shared）
# ==========================================
from backend_shared.application.logging import setup_logging

from app.config.settings import settings
from app.api.routers.ingest.router import router as ingest_router
from app.api.routers.forecast.router import router as forecast_router
from app.api.routers.kpi.router import router as kpi_router
from app.api.routers.external.router import router as external_router
from app.api.routers.calendar.router import router as calendar_router
from app.api.routers.reports import router as reports_router
from app.api.routers.chat.router import router as chat_router
from app.api.routers.analysis.router import router as analysis_router
from app.api.routers.database import router as database_router
from app.api.routers.block_unit_price.router import router as block_unit_price_router
from app.api.routers.manual.router import router as manual_router
from app.api.routers.dashboard.router import router as dashboard_router
from app.api.routers.inbound.router import router as inbound_router
from app.api.routers.sales_tree import router as sales_tree_router
from app.api.routers.auth import router as auth_router
from app.api.routers.health import router as health_router

# ==========================================
# 統一ロギング設定の初期化
# ==========================================
# テクニカルログ基盤: JSON形式、Request ID付与、Uvicorn統合
# 環境変数 LOG_LEVEL で制御可能（DEBUG/INFO/WARNING/ERROR/CRITICAL）
setup_logging()

from backend_shared.application.logging import get_module_logger
logger = get_module_logger(__name__)

# ==========================================
# FastAPI アプリケーション初期化
# ==========================================
# root_path: リバースプロキシ(nginx)経由でのパスプレフィックス対応
# 例: https://example.com/core_api/* → 本アプリケーションにルーティング

app = FastAPI(
    title=settings.API_TITLE,
    description="BFF/Facade API for frontend - handles sync calls and job queuing",
    version=settings.API_VERSION,
    root_path="/core_api",  # リバースプロキシ対応: /core_api/* でアクセス可能
    # 本番環境（DEBUG=False）では /docs と /redoc を無効化
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

logger.info(
    f"Core API initialized (DEBUG={settings.DEBUG}, docs_enabled={settings.DEBUG})",
    extra={"operation": "app_init", "debug": settings.DEBUG}
)

# ==========================================
# Middleware 登録
# ==========================================
# Request ID Middleware: リクエストトレーシング用（backend_shared）
# 全リクエストに X-Request-ID を付与し、ログとレスポンスに含める
from backend_shared.infra.adapters.middleware.request_id import RequestIdMiddleware
app.add_middleware(RequestIdMiddleware)

# Authentication Middleware: IAP 認証を強制（本番環境のみ）
# IAP_ENABLED=true の場合、全てのリクエストで認証を実施
from backend_shared.infra.frameworks.auth_middleware import AuthenticationMiddleware
from app.deps import get_auth_provider

app.add_middleware(
    AuthenticationMiddleware,
    auth_provider_factory=get_auth_provider
    # excluded_paths はデフォルト設定を使用
)

# ==========================================
# CORS設定 (開発モード用)
# ==========================================
from backend_shared.infra.frameworks.cors_config import setup_cors
setup_cors(app)

# ==========================================
# ルーター登録
# ==========================================
# 各機能ごとにルーターを分割し、保守性を向上させる。
# プレフィックス(/forecast, /kpi等)は各ルーターファイル内で定義される。

# --- Core機能 ---
app.include_router(health_router)      # ヘルスチェック: サービス稼働状態監視
app.include_router(auth_router)        # 認証: ユーザー情報取得
app.include_router(ingest_router)      # データ取り込み: CSV アップロード、予約登録
app.include_router(forecast_router)    # 予測機能: ジョブ作成、ステータス確認、結果取得
app.include_router(kpi_router)         # KPI集計: ダッシュボード用メトリクス
app.include_router(dashboard_router)   # ダッシュボード: ターゲット/実績データ
app.include_router(inbound_router)     # 搬入データ: 日次データ取得(累積計算対応)
app.include_router(sales_tree_router)  # 売上ツリー分析: サマリー/日次推移データ

# --- 外部サービスプロキシ (BFF) ---
app.include_router(external_router)           # 外部API統合エンドポイント
app.include_router(reports_router)            # BFF: ledger_api レポート生成プロキシ
app.include_router(block_unit_price_router)   # BFF: ledger_api ブロック単価計算プロキシ
app.include_router(manual_router)             # BFF: manual_api マニュアル参照プロキシ
app.include_router(chat_router)               # BFF: rag_api チャット機能プロキシ
app.include_router(analysis_router)           # BFF: ledger_api 分析機能プロキシ (TODO: 未実装)
app.include_router(database_router)           # BFF: sql_api データベース操作プロキシ (TODO: 未実装)

# --- その他 ---
app.include_router(calendar_router)    # カレンダー: 営業日情報等

# ==========================================
# 統一エラーハンドリング登録（backend_shared）
# ==========================================
from backend_shared.infra.frameworks.exception_handlers import register_exception_handlers
register_exception_handlers(app)


@app.get("/healthz", include_in_schema=False, tags=["health"])
@app.get("/health", include_in_schema=False, tags=["health"])
def healthz():
    """
    Health check endpoint.
    Returns 200 if the API is running.
    """
    return {"status": "ok", "service": "core_api"}


@app.get("/", tags=["info"])
def root():
    """
    Root endpoint with API info.
    """
    return {
        "service": "core_api",
        "version": "1.0.0",
        "description": "BFF/Facade API for frontend",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
