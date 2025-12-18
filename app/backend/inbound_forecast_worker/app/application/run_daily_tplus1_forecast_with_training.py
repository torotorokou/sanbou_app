"""
RunDailyTplus1ForecastWithTrainingUseCase: 日次t+1予測（学習込み）
=============================================
手順:
1. workspace作成（/tmp/forecast_jobs/{job_id}/）
2. DBから実績データ取得（品目別、過去365日）→ raw.csv
3. DBから予約データ取得（過去60日+未来7日）→ reserve.csv
4. retrain_and_eval.py --quick で学習→予測
5. 結果CSV読み込み→DBに保存
6. workspace保持（デバッグ用）

Phase 4実装: DB→学習→予測のE2E
- retrain_and_eval.py を --quick で実行
- 品目別データを stg.shogun_final_receive から取得
- 予約データを mart.v_reserve_daily_for_forecast から取得
"""
from __future__ import annotations

import os
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


class RunDailyTplus1ForecastWithTrainingUseCase:
    """日次t+1予測（学習込み）UseCase"""
    
    def __init__(
        self,
        db_session: Session,
        inbound_actuals_exporter,  # InboundActualsExportPort
        reserve_exporter,  # ReserveExportPort
        forecast_result_repo,  # DailyForecastResultRepositoryPort
        retrain_script_path: Path,
        timeout: int = 1800,
    ):
        self._db = db_session
        self._inbound_actuals_exporter = inbound_actuals_exporter
        self._reserve_exporter = reserve_exporter
        self._forecast_result_repo = forecast_result_repo
        self._retrain_script_path = retrain_script_path
        self._timeout = timeout
    
    def execute(
        self,
        target_date: date,
        job_id: UUID,
    ) -> None:
        """
        日次t+1予測（学習込み）を実行
        
        Args:
            target_date: 予測対象日（明日）
            job_id: ジョブID
        
        Raises:
            Exception: データ取得エラー、学習エラー、予測エラー等
        """
        logger.info(
            f"🚀 Starting daily t+1 forecast with training",
            extra={
                "target_date": str(target_date),
                "job_id": str(job_id)
            }
        )
        
        # 1. workspace作成
        workspace = Path(f"/tmp/forecast_jobs/{job_id}")
        workspace.mkdir(parents=True, exist_ok=True)
        out_dir = workspace / "out"
        out_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 Created workspace: {workspace}")
        
        try:
            # 2. DBから実績データ取得（品目別、過去365日）
            actuals_start = target_date - timedelta(days=365)
            actuals_end = target_date - timedelta(days=1)  # 昨日まで
            
            logger.info(
                f"📊 Exporting actuals: {actuals_start} to {actuals_end}"
            )
            
            actuals_df = self._inbound_actuals_exporter.export_item_level_actuals(
                start_date=actuals_start,
                end_date=actuals_end
            )
            
            if actuals_df.empty:
                raise ValueError(
                    f"No actuals found between {actuals_start} and {actuals_end}"
                )
            
            # raw.csv保存（日本語ヘッダ）
            raw_csv_path = workspace / "raw.csv"
            actuals_df.to_csv(raw_csv_path, index=False, encoding="utf-8")
            
            logger.info(
                f"✅ Exported {len(actuals_df)} actuals to {raw_csv_path}",
                extra={
                    "actuals_count": len(actuals_df),
                    "actuals_max_date": str(actuals_df["伝票日付"].max())
                }
            )
            
            # 3. DBから予約データ取得（過去60日+未来7日）
            reserve_start = target_date - timedelta(days=60)
            reserve_end = target_date + timedelta(days=7)
            
            logger.info(
                f"📅 Exporting reserve: {reserve_start} to {reserve_end}"
            )
            
            reserve_df = self._reserve_exporter.export_daily_reserve(
                start_date=reserve_start,
                end_date=reserve_end
            )
            
            # reserve.csv保存（日本語ヘッダ）
            reserve_csv_path = workspace / "reserve.csv"
            reserve_df.to_csv(reserve_csv_path, index=False, encoding="utf-8")
            
            logger.info(
                f"✅ Exported {len(reserve_df)} reserve records to {reserve_csv_path}",
                extra={"reserve_count": len(reserve_df)}
            )
            
            # 4. retrain_and_eval.py --quick で学習→予測
            pred_out_csv = workspace / "tplus1_pred.csv"
            log_file = workspace / "run.log"
            
            cmd = [
                "python3",
                str(self._retrain_script_path),
                "--quick",
                "--raw-csv", str(raw_csv_path),
                "--reserve-csv", str(reserve_csv_path),
                "--out-dir", str(out_dir),
                "--pred-out-csv", str(pred_out_csv),
                "--start-date", str(target_date),
                "--log", str(log_file),
            ]
            
            logger.info(
                f"🔄 Running retrain_and_eval: {' '.join(cmd[:5])}...",
                extra={"full_command": ' '.join(cmd)}
            )
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout
            )
            
            if result.returncode != 0:
                # ログファイル末尾を取得
                error_detail = ""
                if log_file.exists():
                    with open(log_file, "r") as f:
                        lines = f.readlines()
                        error_detail = "".join(lines[-50:])  # 末尾50行
                
                raise RuntimeError(
                    f"retrain_and_eval.py failed with rc={result.returncode}\n"
                    f"stdout: {result.stdout}\n"
                    f"stderr: {result.stderr}\n"
                    f"log tail:\n{error_detail}"
                )
            
            logger.info(
                f"✅ retrain_and_eval completed successfully",
                extra={"returncode": result.returncode}
            )
            
            # 5. 結果CSV読み込み→DBに保存
            if not pred_out_csv.exists():
                raise FileNotFoundError(
                    f"Prediction output not found: {pred_out_csv}"
                )
            
            pred_df = pd.read_csv(pred_out_csv)
            
            if pred_df.empty:
                raise ValueError("Prediction CSV is empty")
            
            # CSVから予測値を取得（retrain_and_evalの出力形式に依存）
            # 想定: date, y_pred 等のカラム
            # とりあえず最初の行を取得
            p50 = float(pred_df.iloc[0].get("y_pred", pred_df.iloc[0].iloc[-1]))
            p10 = None  # retrain_and_evalが区間予測を出力していれば取得
            p90 = None
            
            logger.info(
                f"📈 Prediction result: p50={p50:.3f}",
                extra={"p50": p50, "p10": p10, "p90": p90}
            )
            
            # input_snapshot作成
            input_snapshot = {
                "actuals_start_date": str(actuals_start),
                "actuals_end_date": str(actuals_end),
                "actuals_count": len(actuals_df),
                "reserve_exists": len(reserve_df) > 0,
                "reserve_count": len(reserve_df),
                "model_version": "final_fast_balanced",
                "training_mode": "quick",
                "workspace": str(workspace),
            }
            
            # DBに保存
            self._forecast_result_repo.save_result(
                target_date=target_date,
                job_id=job_id,
                p50=p50,
                p10=p10,
                p90=p90,
                unit="ton",
                input_snapshot=input_snapshot
            )
            
            logger.info(
                f"✅ Saved prediction result to DB",
                extra={
                    "target_date": str(target_date),
                    "job_id": str(job_id),
                    "p50": p50
                }
            )
        
        except Exception as e:
            logger.error(
                f"❌ Forecast with training failed",
                exc_info=True,
                extra={
                    "target_date": str(target_date),
                    "job_id": str(job_id),
                    "workspace": str(workspace),
                    "error": str(e)
                }
            )
            raise
