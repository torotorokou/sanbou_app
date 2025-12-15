#!/usr/bin/env python3
"""
Inbound Forecast Worker - メインエントリポイント

責務:
  - 需要予測ジョブをrun-to-completion方式で実行
  - Clean ArchitectureのUseCaseを使用
  - 結果をDBに保存（冪等性保証）
  
実行方法:
  python -m worker.main --job-type daily --target-date 2025-01-15
  
設計方針:
  - Clean Architecture: UseCase経由で予測実行
  - 冪等性: 同じ日付の予測を複数回実行しても結果が一貫
  - 失敗時は終了コード非0で明示的に報告
"""
import sys
import os
import argparse
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

# Clean Architecture layers
from app.core.domain.prediction.entities import DailyForecastRequest, PredictionOutput
from app.core.usecases.execute_daily_forecast_uc import ExecuteDailyForecastUseCase
from app.infra.prediction.script_executor import ScriptBasedPredictionExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ForecastWorkerConfig:
    """Worker設定"""
    def __init__(self):
        self.backend_root = Path("/backend")
        # 新しいパス: app/infra/scripts/
        self.scripts_dir = self.backend_root / "app" / "infra" / "scripts"
        
        # 後方互換性: 旧パスもチェック
        if not self.scripts_dir.exists():
            old_scripts_dir = self.backend_root / "scripts"
            if old_scripts_dir.exists():
                logger.warning(f"Using legacy scripts directory: {old_scripts_dir}")
                self.scripts_dir = old_scripts_dir
        
    def validate(self) -> tuple[bool, Optional[str]]:
        """設定の妥当性検証"""
        if not self.scripts_dir.exists():
            return False, f"Scripts directory not found: {self.scripts_dir}"
        return True, None


class ForecastWorker:
    """需要予測Worker"""
    
    def __init__(self, config: ForecastWorkerConfig):
        self.config = config
        
        # DB接続文字列を環境変数から取得
        db_connection_string = self._build_db_connection_string()
        
        # Dependency Injection: UseCase を構築
        prediction_executor = ScriptBasedPredictionExecutor(
            scripts_dir=self.config.scripts_dir,
            db_connection_string=db_connection_string,
            enable_db_save=True,
        )
        self.forecast_usecase = ExecuteDailyForecastUseCase(prediction_executor)
    
    def _build_db_connection_string(self) -> Optional[str]:
        """
        環境変数からDB接続文字列を構築
        
        Returns:
            DB接続文字列（postgresql://...）
        """
        import urllib.parse
        
        host = os.getenv("POSTGRES_HOST", "db")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "myuser")
        password = os.getenv("POSTGRES_PASSWORD", "")
        database = os.getenv("POSTGRES_DB", "sanbou_dev")
        
        if not password:
            logger.warning("POSTGRES_PASSWORD not set. DB save will be disabled.")
            return None
        
        # パスワードをURLエンコード
        encoded_password = urllib.parse.quote_plus(password)
        
        return f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
        
    def run_daily_forecast(
        self,
        target_date: Optional[date] = None,
        future_days: int = 1,
    ) -> tuple[bool, str]:
        """
        日次予測を実行
        
        Args:
            target_date: 予測対象日（Noneの場合は翌日）
            future_days: 予測日数
            
        Returns:
            tuple[bool, str]: (成功フラグ, メッセージ)
        """
        logger.info(f"Starting daily forecast: target_date={target_date}, future_days={future_days}")
        
        try:
            # ドメインエンティティを構築
            request = DailyForecastRequest(target_date=target_date)
            
            # UseCase経由で予測実行
            output: PredictionOutput = self.forecast_usecase.execute(request)
            
            logger.info(f"Forecast completed successfully: {output.csv_path}")
            if output.predictions:
                logger.info(f"Generated {len(output.predictions)} prediction results")
            
            return True, f"Forecast completed: {output.csv_path}"
            
        except Exception as e:
            logger.error(f"Forecast failed: {e}", exc_info=True)
            return False, f"Forecast failed: {str(e)}"


def main():
    """メインエントリポイント"""
    parser = argparse.ArgumentParser(description="Inbound Forecast Worker")
    parser.add_argument(
        "--job-type",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Job type (default: daily)"
    )
    parser.add_argument(
        "--target-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        help="Target date for prediction (YYYY-MM-DD). Default: tomorrow"
    )
    parser.add_argument(
        "--future-days",
        type=int,
        default=1,
        help="Number of days to predict (default: 1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (validation only)"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Inbound Forecast Worker Starting")
    logger.info(f"Job Type: {args.job_type}")
    logger.info(f"Target Date: {args.target_date or 'tomorrow'}")
    logger.info("="*60)
    
    # 設定検証
    config = ForecastWorkerConfig()
    is_valid, error_msg = config.validate()
    
    if not is_valid:
        logger.error(f"Configuration validation failed: {error_msg}")
        sys.exit(1)
    
    if args.dry_run:
        logger.info("Dry run mode - configuration valid")
        sys.exit(0)
    
    # Workerインスタンス作成
    worker = ForecastWorker(config)
    
    # ジョブ実行
    if args.job_type == "daily":
        success, message = worker.run_daily_forecast(
            target_date=args.target_date,
            future_days=args.future_days,
        )
    else:
        logger.error(f"Job type '{args.job_type}' not yet implemented")
        sys.exit(1)
    
    # 結果報告
    if success:
        logger.info(f"✅ Job completed successfully: {message}")
        sys.exit(0)
    else:
        logger.error(f"❌ Job failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
