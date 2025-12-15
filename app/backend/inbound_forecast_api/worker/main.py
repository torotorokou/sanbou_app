#!/usr/bin/env python3
"""
Inbound Forecast Worker - メインエントリポイント

責務:
  - 需要予測ジョブをrun-to-completion方式で実行
  - 既存の予測スクリプト（daily_tplus1_predict.py）をラップ
  - 結果をDBに保存（冪等性保証）
  
実行方法:
  python -m worker.main --job-type daily --target-date 2025-01-15
  
設計方針:
  - SQL直書き禁止（将来的にRepository経由に移行）
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
import subprocess

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
        self.model_bundle = self.backend_root / "data/output/final_fast_balanced/model_bundle.joblib"
        self.res_walk_csv = self.backend_root / "data/output/final_fast_balanced/res_walkforward.csv"
        self.output_dir = self.backend_root / "output"
        self.scripts_dir = self.backend_root / "scripts"
        
    def validate(self) -> tuple[bool, Optional[str]]:
        """設定の妥当性検証"""
        if not self.model_bundle.exists():
            return False, f"Model bundle not found: {self.model_bundle}"
        if not self.res_walk_csv.exists():
            return False, f"History CSV not found: {self.res_walk_csv}"
        if not self.scripts_dir.exists():
            return False, f"Scripts directory not found: {self.scripts_dir}"
        return True, None


class ForecastWorker:
    """需要予測Worker"""
    
    def __init__(self, config: ForecastWorkerConfig):
        self.config = config
        
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
        
        # 出力CSVパス
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = self.config.output_dir / f"tplus1_pred_{timestamp}.csv"
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 既存スクリプトを呼び出し
        cmd = [
            sys.executable,
            str(self.config.scripts_dir / "daily_tplus1_predict.py"),
            "--bundle", str(self.config.model_bundle),
            "--res-walk-csv", str(self.config.res_walk_csv),
            "--out-csv", str(output_csv),
        ]
        
        if target_date:
            cmd.extend(["--start-date", target_date.isoformat()])
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5分タイムアウト
            )
            
            logger.info(f"Prediction completed successfully")
            logger.debug(f"STDOUT: {result.stdout}")
            
            # 出力ファイルの存在確認
            if not output_csv.exists():
                return False, f"Output CSV not generated: {output_csv}"
            
            # TODO: DBに結果を保存（将来実装）
            # self._save_to_db(output_csv, target_date)
            
            return True, f"Prediction saved to {output_csv}"
            
        except subprocess.TimeoutExpired:
            logger.error("Prediction script timed out")
            return False, "Prediction script timed out after 5 minutes"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Prediction script failed with exit code {e.returncode}")
            logger.error(f"STDERR: {e.stderr}")
            return False, f"Prediction script failed: {e.stderr[:500]}"
            
        except Exception as e:
            logger.exception("Unexpected error during prediction")
            return False, f"Unexpected error: {str(e)}"
    
    def _save_to_db(self, csv_path: Path, target_date: Optional[date]):
        """
        予測結果をDBに保存（将来実装）
        
        TODO: 
          - CSV読み込み
          - forecast.predictions_daily テーブルにUPSERT
          - 冪等性保証（同じ日付は上書き）
        """
        logger.warning("DB save not yet implemented - CSV only")
        pass


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
