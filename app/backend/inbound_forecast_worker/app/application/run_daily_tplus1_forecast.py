"""
RunDailyTplus1ForecastUseCase: 日次t+1予測の実行
=============================================
手順:
1. DBから実績データ取得（過去365日）
2. DBから予約データ取得（明日1日分）
3. 既存スクリプト（serve_predict_model_v4_2_4.py）を使用して予測
4. 結果をDBに保存

Phase 1実装: 最小限で動かす
- まずは既存CSVベースのスクリプトを subprocess で呼び出す
- 入力: DBから取得したデータを一時CSVに書き出す
- 出力: スクリプトが生成したCSVを読み込み、DBに保存

Phase 2実装（将来）:
- 推論ロジックを Python モジュールとして直接呼び出す
- CSV経由を廃止
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

import pandas as pd

from backend_shared.application.logging import get_module_logger
from ..ports.inbound_actual_repository import InboundActualRepositoryPort
from ..ports.reserve_daily_repository import ReserveDailyRepositoryPort
from ..ports.forecast_result_repository import (
    ForecastResultRepositoryPort,
    DailyForecastResult
)

logger = get_module_logger(__name__)


class RunDailyTplus1ForecastUseCase:
    """日次t+1予測の実行UseCase"""
    
    def __init__(
        self,
        inbound_actual_repo: InboundActualRepositoryPort,
        reserve_daily_repo: ReserveDailyRepositoryPort,
        forecast_result_repo: ForecastResultRepositoryPort,
        model_bundle_path: Path,
        res_walk_csv_path: Path,
        script_path: Path,
        timeout: int = 1800,
    ):
        self._inbound_actual_repo = inbound_actual_repo
        self._reserve_daily_repo = reserve_daily_repo
        self._forecast_result_repo = forecast_result_repo
        self._model_bundle_path = model_bundle_path
        self._res_walk_csv_path = res_walk_csv_path
        self._script_path = script_path
        self._timeout = timeout
    
    def execute(
        self,
        target_date: date,
        job_id: UUID,
    ) -> DailyForecastResult:
        """
        日次t+1予測を実行
        
        Args:
            target_date: 予測対象日（明日）
            job_id: ジョブID
        
        Returns:
            DailyForecastResult: 予測結果
        
        Raises:
            Exception: データ取得エラー、予測エラー等
        """
        logger.info(
            f"Starting daily t+1 forecast: target_date={target_date}, job_id={job_id}"
        )
        
        # 1. DBから実績データ取得（過去365日）
        from_date = target_date - timedelta(days=365)
        to_date = target_date - timedelta(days=1)  # 昨日まで
        
        logger.info(f"Fetching inbound actuals: {from_date} to {to_date}")
        actuals = self._inbound_actual_repo.get_daily_actuals(from_date, to_date)
        
        if not actuals:
            raise ValueError(f"No actual data found between {from_date} and {to_date}")
        
        actuals_max_date = max(a.ddate for a in actuals)
        logger.info(f"Fetched {len(actuals)} actual records, max_date={actuals_max_date}")
        
        # 2. DBから予約データ取得（明日1日分）
        logger.info(f"Fetching reserve data for {target_date}")
        reserves = self._reserve_daily_repo.get_reserve_daily(target_date, target_date)
        
        reserve_exists = len(reserves) > 0
        reserve_trucks = reserves[0].reserve_trucks if reserve_exists else 0
        reserve_fixed_ratio = float(reserves[0].reserve_fixed_ratio) if reserve_exists else 0.0
        
        logger.info(
            f"Reserve data: exists={reserve_exists}, "
            f"trucks={reserve_trucks}, fixed_ratio={reserve_fixed_ratio}"
        )
        
        # 3. 既存スクリプトを使用して予測
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # 予約データを一時CSVに保存（あれば）
            reserve_csv_path = None
            if reserve_exists:
                reserve_csv_path = tmpdir_path / "reserve.csv"
                reserve_df = pd.DataFrame([{
                    "予約日": r.date,
                    "台数": r.reserve_trucks,
                    "固定客": 1 if r.reserve_fixed_ratio > 0.5 else 0,
                } for r in reserves])
                reserve_df.to_csv(reserve_csv_path, index=False, encoding="utf-8")
                logger.debug(f"Saved reserve data to {reserve_csv_path}")
            
            # 出力CSV
            output_csv_path = tmpdir_path / "tplus1_pred.csv"
            
            # コマンド構築
            cmd = [
                "python3",
                str(self._script_path),
                "--bundle", str(self._model_bundle_path),
                "--res-walk-csv", str(self._res_walk_csv_path),
                "--out-csv", str(output_csv_path),
                "--start-date", target_date.isoformat(),
            ]
            
            if reserve_csv_path:
                cmd += [
                    "--reserve-csv", str(reserve_csv_path),
                    "--reserve-date-col", "予約日",
                    "--reserve-count-col", "台数",
                    "--reserve-fixed-col", "固定客",
                ]
            
            logger.info(f"Executing prediction script: {' '.join(cmd)}")
            
            # subprocess 実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
                cwd="/backend"
            )
            
            # stdout/stderr をログに記録
            if result.stdout:
                logger.info(f"Script stdout: {result.stdout[:1000]}")
            if result.stderr:
                logger.warning(f"Script stderr: {result.stderr[:1000]}")
            
            # リターンコードチェック
            if result.returncode != 0:
                raise RuntimeError(
                    f"Prediction script failed with code {result.returncode}. "
                    f"stderr: {result.stderr[:500]}"
                )
            
            # 出力CSV確認
            if not output_csv_path.exists() or output_csv_path.stat().st_size == 0:
                raise RuntimeError(f"Output CSV not created or empty: {output_csv_path}")
            
            # CSVを読み込み
            logger.info(f"Reading prediction results from {output_csv_path}")
            pred_df = pd.read_csv(output_csv_path)
            
            # 結果抽出（最初の行を使用）
            if len(pred_df) == 0:
                raise RuntimeError("Prediction CSV is empty")
            
            row = pred_df.iloc[0]
            
            # p50, p90 等を抽出（カラム名は serve_predict_model_v4_2_4.py の出力に依存）
            # 実際のカラム名を確認して調整が必要
            p50 = Decimal(str(row.get("p50", row.get("total_pred", 0))))
            p10 = Decimal(str(row.get("p10", 0))) if "p10" in row else None
            p90 = Decimal(str(row.get("p90", 0))) if "p90" in row else None
            
            logger.info(f"Prediction results: p50={p50}, p10={p10}, p90={p90}")
        
        # 4. input_snapshot を構築
        input_snapshot = {
            "actuals_max_date": str(actuals_max_date),
            "actuals_count": len(actuals),
            "reserve_exists": reserve_exists,
            "reserve_trucks": reserve_trucks,
            "reserve_fixed_ratio": reserve_fixed_ratio,
            "model_version": self._model_bundle_path.parent.name,
            "from_date": str(from_date),
            "to_date": str(to_date),
        }
        
        # 5. 結果をDBに保存
        forecast_result = DailyForecastResult(
            target_date=target_date,
            job_id=job_id,
            p50=p50,
            p10=p10,
            p90=p90,
            unit="ton",
            input_snapshot=input_snapshot,
        )
        
        result_id = self._forecast_result_repo.save_daily_forecast(forecast_result)
        
        logger.info(
            f"✅ Daily t+1 forecast completed: "
            f"target_date={target_date}, result_id={result_id}, p50={p50}"
        )
        
        return forecast_result
