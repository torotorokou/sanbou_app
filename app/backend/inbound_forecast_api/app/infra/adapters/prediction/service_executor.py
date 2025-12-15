"""
Service-Based Prediction Executor

InferenceServiceを使用して予測を実行するアダプター。
subprocessを使わずに直接サービスを呼び出す。

設計方針:
- InferenceServiceを使用してsubprocess不要に
- ScriptBasedPredictionExecutorと同じインターフェース
- 段階的な移行を可能にする
"""
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import pandas as pd

from app.core.domain.prediction import (
    DailyForecastRequest,
    PredictionOutput,
    PredictionResult,
)
from app.infra.services.prediction.inference_service import InferenceService

logger = logging.getLogger(__name__)


class ServiceBasedPredictionExecutor:
    """
    InferenceServiceを使用した予測実行アダプター。
    
    ScriptBasedPredictionExecutorの代替実装。
    subprocessではなく直接サービスを呼び出すため：
    - 型安全性が向上
    - パフォーマンスが向上
    - エラーハンドリングが簡潔に
    
    Example:
        >>> executor = ServiceBasedPredictionExecutor(
        ...     model_bundle_path=Path("/backend/model.joblib")
        ... )
        >>> request = DailyForecastRequest(target_date=date(2025, 1, 22))
        >>> output = executor.execute_daily_forecast(request)
        >>> print(output.csv_path)
    """
    
    def __init__(
        self,
        model_bundle_path: Path,
        output_dir: Path,
        res_walk_csv: Optional[Path] = None,
        db_connection_string: Optional[str] = None,
        enable_db_save: bool = True,
    ):
        """
        Args:
            model_bundle_path: モデルバンドルファイル（.joblib）のパス
            output_dir: 出力CSVを保存するディレクトリ
            res_walk_csv: 履歴CSV（res_walkforward.csv）のパス
            db_connection_string: DB接続文字列（DB保存用）
            enable_db_save: DB保存を有効にするか
        """
        self.model_bundle_path = model_bundle_path
        self.output_dir = output_dir
        self.res_walk_csv = res_walk_csv
        self.db_connection_string = db_connection_string
        self.enable_db_save = enable_db_save
        
        # InferenceServiceのインスタンス化
        self.inference_service = InferenceService(
            model_bundle_path=model_bundle_path,
            res_walk_csv=res_walk_csv,
        )
        
        logger.info(f"✅ ServiceBasedPredictionExecutor initialized: bundle={model_bundle_path}")
    
    def execute_daily_forecast(self, request: DailyForecastRequest) -> PredictionOutput:
        """
        日次予測を実行。
        
        Args:
            request: 予測リクエスト（DailyForecastRequest）
            
        Returns:
            PredictionOutput: 予測実行の結果
                - csv_path: 生成されたCSVファイルのパス
                - predictions: 予測結果のリスト（オプション）
            
        Raises:
            FileNotFoundError: 必要なファイルが見つからない
            RuntimeError: 予測実行に失敗
        """
        # 出力CSVパス
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = self.output_dir / f"tplus1_pred_{timestamp}.csv"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"🚀 Executing daily forecast: target_date={request.target_date}")
            
            # InferenceServiceを使用して予測を実行
            result_df = self.inference_service.predict(
                output_csv_path=output_csv,
                start_date=request.target_date,
                future_days=1,
                reserve_csv=None,  # TODO: 予約データの処理
                reserve_default_count=0.0,
                reserve_default_sum=0.0,
                reserve_default_fixed=0.0,
            )
            
            logger.info(f"✅ CSV generated: {output_csv}")
            
            # DB保存（有効な場合）
            if self.enable_db_save and self.db_connection_string:
                try:
                    self._save_predictions_to_db(output_csv, request.target_date)
                except Exception as e:
                    logger.error(f"Failed to save predictions to DB: {e}", exc_info=True)
                    # DB保存失敗してもCSVは生成済みなので続行
            
            # PredictionOutputを生成して返却
            return PredictionOutput(
                csv_path=str(output_csv),
                predictions=None  # 将来実装: result_df → PredictionResult変換
            )
            
        except Exception as e:
            logger.error(f"Daily forecast failed: {e}", exc_info=True)
            raise RuntimeError(f"Daily forecast execution failed: {e}") from e
    
    def _save_predictions_to_db(self, csv_path: Path, prediction_date: Optional[date]):
        """
        予測結果をDBに保存（UPSERT）
        
        Args:
            csv_path: 予測結果CSVのパス
            prediction_date: 予測日
        """
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        # CSV読み込み
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV: {len(df)} rows, columns={list(df.columns)}")
        
        # 予測日の抽出
        if prediction_date is None and 'date' in df.columns:
            prediction_date = pd.to_datetime(df['date'].iloc[0]).date()
        
        if prediction_date is None:
            logger.warning("No prediction_date provided and CSV has no 'date' column. Skipping DB save.")
            return
        
        # DB接続
        engine = create_engine(self.db_connection_string, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        try:
            # スキーマ設定
            session.execute(text("SET search_path TO forecast, public"))
            
            # UPSERT処理（既存行を削除してINSERT）
            delete_stmt = text(
                "DELETE FROM forecast.predictions_daily WHERE date = :pred_date"
            )
            session.execute(delete_stmt, {"pred_date": prediction_date})
            
            # 必要なカラムのマッピング
            if 'total_pred' not in df.columns:
                logger.warning(f"CSV missing 'total_pred' column. Available: {list(df.columns)}")
                return
            
            # 代表行を取得
            row = df.iloc[0]
            
            insert_stmt = text("""
                INSERT INTO forecast.predictions_daily 
                (date, y_hat, y_lo, y_hi, model_version, generated_at)
                VALUES 
                (:date, :y_hat, :y_lo, :y_hi, :model_version, NOW())
            """)
            
            session.execute(insert_stmt, {
                "date": prediction_date,
                "y_hat": float(row.get('total_pred', 0)),
                "y_lo": float(row.get('total_pred_low_1sigma', 0)),
                "y_hi": float(row.get('total_pred_high_1sigma', 0)),
                "model_version": "v1_daily_tplus1_service",
            })
            
            session.commit()
            logger.info(f"✅ Saved prediction to DB: date={prediction_date}, y_hat={row.get('total_pred')}")
            
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"DB save failed: {e}") from e
        finally:
            session.close()
