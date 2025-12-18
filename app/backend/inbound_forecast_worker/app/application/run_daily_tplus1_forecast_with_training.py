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
            
            # 実績データの検証
            actuals_max_date = actuals_df["伝票日付"].max()
            avg_weight = actuals_df["正味重量"].mean()
            
            if actuals_max_date != actuals_end:
                logger.warning(
                    f"⚠️ Actuals max date mismatch: expected {actuals_end}, got {actuals_max_date}"
                )
            
            if avg_weight < 0.01 or avg_weight > 50:
                logger.error(
                    f"❌ Suspicious average weight: {avg_weight:.3f} ton (expected 0.5～5.0)"
                )
                raise ValueError(f"Invalid average weight: {avg_weight:.3f} ton")
            
            logger.info(
                f"✅ Actuals data prepared: {len(actuals_df)} records",
                extra={
                    "actuals_count": len(actuals_df),
                    "actuals_max_date": str(actuals_max_date),
                    "avg_weight_ton": round(avg_weight, 3)
                }
            )
            
            # 3. DBから予約データ取得（過去360日、target_date当日まで）
            # 注意: 学習に必要な期間を確保（train_daily_model.pyで使用）
            reserve_start = target_date - timedelta(days=360)
            reserve_end = target_date  # target_date当日まで（予測に使用）
            
            logger.info(
                f"📅 Preparing reserve data range: {reserve_start} to {reserve_end}"
            )
            
            # 予約データの検証ログのみ出力（CSV保存は廃止）
            reserve_df = self._reserve_exporter.export_daily_reserve(
                start_date=reserve_start,
                end_date=reserve_end
            )
            
            if not reserve_df.empty:
                reserve_dates = pd.to_datetime(reserve_df["予約日"]).dt.date
                target_date_exists = target_date in reserve_dates.values
                if not target_date_exists:
                    logger.warning(
                        f"⚠️ Reserve data for target_date {target_date} does not exist. "
                        f"Max reserve date: {reserve_dates.max()}"
                    )
            else:
                logger.warning("⚠️ Reserve data is empty")
            
            logger.info(
                f"✅ Reserve data prepared: {len(reserve_df)} records",
                extra={
                    "reserve_count": len(reserve_df),
                    "reserve_max_date": str(reserve_df["予約日"].max()) if not reserve_df.empty else "N/A"
                }
            )
            
            # 4. retrain_and_eval.py --quick で学習→予測（DB直接取得モード）
            pred_out_csv = workspace / "tplus1_pred.csv"
            log_file = workspace / "run.log"
            
            # DB接続文字列の取得（backend_sharedのurl_builderを使用）
            from backend_shared.db.url_builder import build_database_url
            db_url = build_database_url(driver="psycopg", raise_on_missing=True)
            
            cmd = [
                "python3",
                str(self._retrain_script_path),
                "--quick",
                "--use-db",  # CSV廃止：DB直接取得モード
                "--db-connection-string", db_url,
                "--actuals-start-date", str(actuals_start),
                "--actuals-end-date", str(actuals_end),
                "--reserve-start-date", str(reserve_start),
                "--reserve-end-date", str(reserve_end),
                "--out-dir", str(out_dir),
                "--pred-out-csv", str(pred_out_csv),
                "--start-date", str(target_date),
                "--end-date", str(target_date),  # 1日のみ予測（必須）
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
            
            # CSVから予測値を取得（p50列を優先、なければtotal_pred）
            first_row = pred_df.iloc[0]
            if "p50" in pred_df.columns:
                p50 = float(first_row["p50"])
            elif "total_pred" in pred_df.columns:
                p50 = float(first_row["total_pred"])
            else:
                raise ValueError(f"Required column 'p50' or 'total_pred' not found. Columns: {pred_df.columns.tolist()}")
            
            # p10/p90も取得（存在する場合）
            # 注意: CSV列は異なる意味を持つ
            #   - "p50", "p90": quantile回帰による50%/90%分位点
            #   - "total_pred_low_1sigma", "total_pred_high_1sigma": total_pred ± 1σ
            # DBには本来のquantile値を保存すべき
            p10 = None
            p90 = None
            
            # quantile回帰の値を優先使用
            if "p50" in pred_df.columns and "p90" in pred_df.columns:
                # p90からσを逆算してp10を推定 (p90 = p50 + 1.28σ と仮定)
                p90_raw = float(first_row["p90"])
                if p90_raw > p50:
                    z90 = 1.2815515655446004  # 80%分位点のz値
                    sigma = (p90_raw - p50) / z90
                    z10 = -1.2815515655446004  # 20%分位点のz値
                    p10 = max(0.0, p50 + z10 * sigma)
                    p90 = p90_raw
                else:
                    # p90がp50以下の場合 (zero_cap等でキャップされた場合)
                    # σベースの値を使用
                    if "total_pred_low_1sigma" in pred_df.columns and "total_pred_high_1sigma" in pred_df.columns:
                        p10 = float(first_row["total_pred_low_1sigma"])
                        p90 = float(first_row["total_pred_high_1sigma"])
            elif "total_pred_low_1sigma" in pred_df.columns and "total_pred_high_1sigma" in pred_df.columns:
                # quantile値がない場合はσベースの値を使用（互換性のため）
                p10 = float(first_row["total_pred_low_1sigma"])
                p90 = float(first_row["total_pred_high_1sigma"])
            
            # 異常値チェック
            if p50 < 1.0 or p50 > 200.0:
                logger.warning(
                    f"⚠️ Prediction value out of reasonable range: p50={p50:.3f} ton",
                    extra={"p50": p50, "min_expected": 1.0, "max_expected": 200.0}
                )
            
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
