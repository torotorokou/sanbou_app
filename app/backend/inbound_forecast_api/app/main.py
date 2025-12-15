"""
Main application entry point

FastAPIアプリケーションのセットアップと起動。
"""
import logging

from fastapi import FastAPI

from app.api.routers import prediction, forecast_results

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    FastAPIアプリケーションを作成する。
    
    Returns:
        FastAPI: 設定済みのFastAPIアプリケーション
    """
    app = FastAPI(
        title="Inbound Forecast API",
        description="需要予測サービス - 日次/週次/月次の予測を提供",
        version="1.0.0",
    )
    
    # ルーターを登録
    app.include_router(prediction.router, tags=["prediction"])
    app.include_router(forecast_results.router)  # Phase 1: Results viewing
    
    # Startup/Shutdown イベント
    @app.on_event("startup")
    async def startup_event():
        """アプリケーション起動時の処理"""
        logger.info("🚀 Inbound Forecast API starting up...")
        
        # TODO: モデルバンドルの事前読み込み
        # bundle_path = Path("/backend/data/output/final_fast_balanced/model_bundle.joblib")
        # if bundle_path.exists():
        #     logger.info(f"Loading model bundle from {bundle_path}")
        #     # Load model bundle here
        # else:
        #     logger.warning(f"Model bundle not found: {bundle_path}")
        
        logger.info("✅ Inbound Forecast API ready")

    @app.on_event("shutdown")
    async def shutdown_event():
        """アプリケーション終了時の処理"""
        logger.info("🛑 Inbound Forecast API shutting down...")
    
    return app


# アプリケーションインスタンスを作成
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
