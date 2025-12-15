"""
Script-Based Prediction Executor

既存の daily_tplus1_predict.py を subprocess で実行する Adapter。
"""
import subprocess
import os
from datetime import datetime
from datetime import date
from typing import Optional
from pathlib import Path


class ScriptBasedPredictionExecutor:
    """
    既存スクリプトを subprocess で実行する Adapter。
    
    将来的に段階的に移行：
    1. subprocess 実行（現在）
    2. スクリプトをモジュール化して import
    3. ライブラリ化して直接呼び出し
    """
    
    def __init__(self, scripts_dir: Path):
        self.scripts_dir = scripts_dir
        self.predict_script = scripts_dir / "daily_tplus1_predict.py"
        
        # 既存のモデルパス（既存worker/main.pyと同じ）
        backend_root = Path("/backend")
        self.model_bundle = backend_root / "data/output/final_fast_balanced/model_bundle.joblib"
        self.res_walk_csv = backend_root / "data/output/final_fast_balanced/res_walkforward.csv"
        self.output_dir = backend_root / "output"
        
    def execute_daily_forecast(self, target_date: Optional[date] = None) -> str:
        """
        日次予測を実行。
        
        Args:
            target_date: 予測対象日（Noneの場合は明日）
            
        Returns:
            生成されたCSVファイルのパス
            
        Raises:
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
        
        cmd = [
            "python",
            str(self.predict_script),
            "--bundle", str(self.model_bundle),
            "--res-walk-csv", str(self.res_walk_csv),
            "--out-csv", str(output_csv),
        ]
        
        if target_date:
            cmd.extend(["--start-date", target_date.isoformat()])
        
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
            
            return str(output_csv)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Prediction script failed: {e.stderr}"
            ) from e
