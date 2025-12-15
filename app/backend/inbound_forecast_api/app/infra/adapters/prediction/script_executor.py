"""
Script-Based Prediction Executor

既存の daily_tplus1_predict.py を subprocess で実行する Adapter。

設計方針:
- ドメインエンティティ（DailyForecastRequest, PredictionOutput）を使用
- 既存スクリプトとの互換性を維持
- 型安全性とバリデーションを提供
"""
import subprocess
import os
import logging
from datetime import datetime, date
from typing import Optional
from pathlib import Path
import pandas as pd

from app.core.domain.prediction import (
    DailyForecastRequest,
    PredictionOutput,
    PredictionResult,
)

logger = logging.getLogger(__name__)


class ScriptBasedPredictionExecutor:
    """
    既存スクリプトを subprocess で実行する Adapter。
    
    将来的に段階的に移行：
    1. subprocess 実行（現在）
    2. スクリプトをモジュール化して import
    3. ライブラリ化して直接呼び出し
    
    Implementation Details:
    - DailyForecastRequestを受け取り、PredictionOutputを返す
    - 既存スクリプト（daily_tplus1_predict.py）をsubprocessで実行
    - CSVファイルとDB保存の両方に対応
    """
    
    def __init__(
        self, 
        scripts_dir: Path,
        db_connection_string: Optional[str] = None,
        enable_db_save: bool = True,
    ):
        self.scripts_dir = scripts_dir
        self.predict_script = scripts_dir / "daily_tplus1_predict.py"
        self.db_connection_string = db_connection_string
        self.enable_db_save = enable_db_save
        
        # 既存のモデルパス（既存worker/main.pyと同じ）
        backend_root = Path("/backend")
        self.model_bundle = backend_root / "data/output/final_fast_balanced/model_bundle.joblib"
        self.res_walk_csv = backend_root / "data/output/final_fast_balanced/res_walkforward.csv"
        self.output_dir = backend_root / "output"
        
    def execute_daily_forecast(self, request: DailyForecastRequest) -> PredictionOutput:
        """
        日次予測を実行。
        
        Args:
            request: 予測リクエスト（DailyForecastRequest）
            
        Returns:
            PredictionOutput: 予測実行の結果
                - csv_path: 生成されたCSVファイルのパス
                - predictions: 予測結果のリスト（オプション、将来実装）
            
        Raises:
            FileNotFoundError: 必要なファイルが見つからない
            RuntimeError: 予測実行に失敗
        """
        if not self.predict_script.exists():
            raise FileNotFoundError(f"Script not found: {self.predict_script}")
        
        if not self.model_bundle.exists():
            raise FileNotFoundError(f"Model bundle not found: {self.model_bundle}")
        
        # 出力CSVパス
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = self.output_dir / f"tplus1_pred_{timestamp}.csv"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # コマンド構築
        cmd = [
            "python",
            str(self.predict_script),
            "--bundle", str(self.model_bundle),
            "--res-walk-csv", str(self.res_walk_csv),
            "--out-csv", str(output_csv),
        ]
        
        # リクエストからパラメータを取得
        if request.target_date:
            cmd.extend(["--start-date", request.target_date.isoformat()])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=str(self.scripts_dir.parent),
                env=os.environ.copy(),
                timeout=300,  # 5分タイムアウト
            )
            
            # 出力ファイルの存在確認
            if not output_csv.exists():
                raise RuntimeError(f"Output CSV not generated: {output_csv}")
            
            logger.info(f"✅ CSV generated: {output_csv}")
            
            # DB保存（有効な場合）
            if self.enable_db_save and self.db_connection_string:
                try:
                    self._save_predictions_to_db(output_csv, request.target_date)
                except Exception as e:
                    logger.error(f"Failed to save predictions to DB: {e}", exc_info=True)
                    # DB保存失敗してもCSVは生成済みなので続行
            
            # PredictionOutputを生成して返却
            # TODO: CSVを読み込んでPredictionResultのリストを生成
            return PredictionOutput(
                csv_path=str(output_csv),
                predictions=None  # 将来実装: CSV読み込み → PredictionResult変換
            )
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Prediction script failed: {e.stderr}"
            ) from e
    
    def _save_predictions_to_db(self, csv_path: Path, prediction_date: Optional[date]):
        """
        予測結果をDBに保存（UPSERT）
        
        Args:
            csv_path: 予測結果CSVのパス
            prediction_date: 予測日（Noneの場合はCSVから抽出）
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
            
            # UPSERT処理（単純化: 既存行を削除してINSERT）
            # TODO: より効率的なUPSERT処理に改善
            delete_stmt = text(
                "DELETE FROM forecast.predictions_daily WHERE date = :pred_date"
            )
            session.execute(delete_stmt, {"pred_date": prediction_date})
            
            # 必要なカラムのマッピング
            # CSV: date, total_pred, total_pred_low_1sigma, total_pred_high_1sigma
            # DB: date, y_hat, y_lo, y_hi, model_version, generated_at
            
            if 'total_pred' not in df.columns:
                logger.warning(f"CSV missing 'total_pred' column. Available: {list(df.columns)}")
                return
            
            # 代表行（通常1行）を取得
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
                "model_version": "v1_daily_tplus1",
            })
            
            session.commit()
            logger.info(f"✅ Saved prediction to DB: date={prediction_date}, y_hat={row.get('total_pred')}")
            
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"DB save failed: {e}") from e
        finally:
            session.close()
