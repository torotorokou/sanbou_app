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
import os
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentation.routers.ingest.router import router as ingest_router
from app.presentation.routers.forecast.router import router as forecast_router
from app.presentation.routers.kpi.router import router as kpi_router
from app.presentation.routers.external.router import router as external_router
from app.presentation.routers.calendar.router import router as calendar_router
from app.presentation.routers.reports.router import router as reports_router
from app.presentation.routers.chat.router import router as chat_router
from app.presentation.routers.analysis.router import router as analysis_router
from app.presentation.routers.database.router import router as database_router
from app.presentation.routers.block_unit_price.router import router as block_unit_price_router
from app.presentation.routers.manual.router import router as manual_router
from app.presentation.routers.dashboard.router import router as dashboard_router
from app.presentation.routers.inbound.router import router as inbound_router
from app.presentation.routers.sales_tree.router import router as sales_tree_router

# ==========================================
# 構造化JSONロギングの設定
# ==========================================
# CloudWatch/Datadogなどのログアグリゲーターでのパースやクエリを容易にするため、
# JSON形式でログを出力する。各ログエントリにはタイムスタンプ、ロガー名、
# ログレベル、メッセージが含まれる。
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# ==========================================
# FastAPI アプリケーション初期化
# ==========================================
# root_path: リバースプロキシ(nginx)経由でのパスプレフィックス対応
# 例: https://example.com/core_api/* → 本アプリケーションにルーティング
app = FastAPI(
    title="Core API",
    description="BFF/Facade API for frontend - handles sync calls and job queuing",
    version="1.0.0",
    root_path="/core_api",  # リバースプロキシ対応: /core_api/* でアクセス可能
)

# ==========================================
# CORS設定 (開発モード用)
# ==========================================
# 開発環境でフロントエンドが別ドメイン(localhost:5173等)で動作する場合に必要。
# 本番環境ではnginxでCORS設定を行うため、通常は無効化する。
# 環境変数 ENABLE_CORS=true で有効化される。
if os.getenv("ENABLE_CORS", "false").lower() == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 開発用: すべてのオリジンを許可(本番では制限すること)
        allow_credentials=True,  # Cookie/認証ヘッダーの送信を許可
        allow_methods=["*"],  # すべてのHTTPメソッドを許可
        allow_headers=["*"],  # すべてのカスタムヘッダーを許可
    )

# ==========================================
# ルーター登録
# ==========================================
# 各機能ごとにルーターを分割し、保守性を向上させる。
# プレフィックス(/forecast, /kpi等)は各ルーターファイル内で定義される。

# --- Core機能 ---
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
# 統一エラーハンドリング登録
# ==========================================
from app.presentation.middleware.error_handler import register_exception_handlers
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
