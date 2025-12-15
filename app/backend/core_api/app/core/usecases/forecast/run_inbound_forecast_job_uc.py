"""
UseCase: RunInboundForecastJobUseCase

搬入量予測ジョブを実行するUseCase。

責務:
  - ジョブをRUNNINGに更新
  - 予測計算を実行（既存スクリプトをラップ）
  - 結果をDBに保存
  - ジョブをSUCCESS/FAILEDに更新
  
設計方針:
  - 既存の予測スクリプト（inbound_forecast_api）を呼び出す形でラップ
  - 冪等性: 同じ期間の予測を複数回実行しても結果が一貫
  - エラーハンドリング: 例外を捕捉してjobをFAILEDにマーク
"""
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional
from datetime import date as date_type

from app.core.ports.forecast_port import IForecastJobRepository

logger = logging.getLogger(__name__)


class RunInboundForecastJobUseCase:
    """
    搬入量予測ジョブ実行UseCase
    
    処理フロー:
      1. ジョブIDでジョブ情報を取得
      2. ジョブをRUNNINGに更新
      3. 既存の予測スクリプトを実行
      4. 成功時: ジョブをSUCCESSに更新
      5. 失敗時: ジョブをFAILEDに更新（error_message記録）
    
    冪等性:
      - 同じ日付の予測を複数回実行してもCSVファイル名がタイムスタンプ付きなので衝突しない
      - 将来的にDB保存時はUPSERT（同じ日付は上書き）で実装予定
    """
    
    def __init__(
        self,
        job_repo: IForecastJobRepository,
        prediction_script_path: Optional[Path] = None,
    ):
        """
        Args:
            job_repo: ジョブ管理リポジトリ
            prediction_script_path: 予測スクリプトのパス（テスト用）
        """
        self._job_repo = job_repo
        # デフォルトのスクリプトパス（コンテナ内の想定パス）
        self._script_path = prediction_script_path or Path(
            "/backend/inbound_forecast_api/scripts/daily_tplus1_predict.py"
        )
    
    def execute(self, job_id: int) -> bool:
        """
        ジョブを実行
        
        Args:
            job_id: 実行するジョブのID
            
        Returns:
            bool: 実行成功時True、失敗時False
            
        Raises:
            ValueError: ジョブが見つからない場合
        """
        # ジョブ取得
        job = self._job_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        logger.info(f"Starting job execution: job_id={job_id}, type={job.job_type}")
        
        # ジョブをRUNNINGに更新
        self._job_repo.mark_running(job_id)
        
        try:
            # 予測実行
            target_date = job.target_from  # 単日予測の場合
            success, message = self._run_prediction(target_date)
            
            if success:
                # 成功: ジョブをSUCCESSに更新
                self._job_repo.mark_done(job_id)
                logger.info(f"Job completed successfully: job_id={job_id}, {message}")
                return True
            else:
                # 失敗: ジョブをFAILEDに更新
                self._job_repo.mark_failed(job_id, message)
                logger.error(f"Job failed: job_id={job_id}, {message}")
                return False
                
        except Exception as e:
            # 予期しないエラー
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"Job execution failed with exception: job_id={job_id}")
            self._job_repo.mark_failed(job_id, error_msg)
            return False
    
    def _run_prediction(
        self,
        target_date: date_type,
    ) -> tuple[bool, str]:
        """
        予測スクリプトを実行
        
        Args:
            target_date: 予測対象日
            
        Returns:
            tuple[bool, str]: (成功フラグ, メッセージ)
        """
        # モデルバンドルのパス（コンテナ内の想定パス）
        model_bundle = Path("/backend/inbound_forecast_api/data/output/final_fast_balanced/model_bundle.joblib")
        res_walk_csv = Path("/backend/inbound_forecast_api/data/output/final_fast_balanced/res_walkforward.csv")
        output_dir = Path("/backend/inbound_forecast_api/output")
        
        # 出力CSVパス（タイムスタンプ付き）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = output_dir / f"tplus1_pred_{timestamp}.csv"
        
        # コマンド構築
        cmd = [
            sys.executable,
            str(self._script_path),
            "--bundle", str(model_bundle),
            "--res-walk-csv", str(res_walk_csv),
            "--out-csv", str(output_csv),
            "--start-date", target_date.isoformat(),
        ]
        
        logger.info(f"Executing prediction: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5分タイムアウト
            )
            
            logger.debug(f"Prediction stdout: {result.stdout}")
            
            # 出力ファイルの存在確認
            if not output_csv.exists():
                return False, f"Output CSV not generated: {output_csv}"
            
            return True, f"Prediction saved to {output_csv}"
            
        except subprocess.TimeoutExpired:
            return False, "Prediction script timed out after 5 minutes"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Prediction script failed (exit code {e.returncode}): {e.stderr[:500]}"
            return False, error_msg
            
        except Exception as e:
            return False, f"Unexpected error during prediction: {str(e)}"
