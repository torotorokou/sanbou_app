"""
Inference Service

serve_predict_model_v4_2_4.py から推論ロジックを抽出したサービスクラス。
CLIに依存せず、直接importして使用可能。

設計方針:
- run_inference 関数をクラスメソッドとしてラップ
- 既存のヘルパー関数群を再利用（import経由）
- 型安全性を提供
- テスト可能な構造
"""
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd

# 既存のヘルパー関数をインポート
import sys
import os

# scriptsディレクトリをパスに追加（既存関数の再利用のため）
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

try:
    from serve_predict_model_v4_2_4 import run_inference as _run_inference_impl
except ImportError:
    _run_inference_impl = None

logger = logging.getLogger(__name__)


class InferenceService:
    """
    推論サービス
    
    既存のrun_inference関数をラップし、Pythonから直接呼び出し可能にする。
    
    Example:
        >>> service = InferenceService(model_bundle_path=Path("/backend/model.joblib"))
        >>> result = service.predict(
        ...     start_date=date(2025, 1, 22),
        ...     future_days=7,
        ...     reserve_csv=Path("/backend/reserve.csv")
        ... )
        >>> print(result)  # pd.DataFrame
    """
    
    def __init__(
        self,
        model_bundle_path: Path,
        res_walk_csv: Optional[Path] = None,
    ):
        """
        Args:
            model_bundle_path: モデルバンドルファイル（.joblib）のパス
            res_walk_csv: 履歴CSV（res_walkforward.csv）のパス（オプション）
        """
        self.model_bundle_path = model_bundle_path
        self.res_walk_csv = res_walk_csv
        
        if not self.model_bundle_path.exists():
            raise FileNotFoundError(f"Model bundle not found: {self.model_bundle_path}")
    
    def predict(
        self,
        output_csv_path: Path,
        start_date: Optional[date] = None,
        future_days: int = 1,
        reserve_csv: Optional[Path] = None,
        reserve_date_col: str = "予約日",
        reserve_count_col: str = "台数",
        reserve_fixed_col: str = "固定客",
        reserve_default_count: float = 0.0,
        reserve_default_sum: float = 0.0,
        reserve_default_fixed: float = 0.0,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        予測を実行してCSVに保存し、結果を返す。
        
        Args:
            output_csv_path: 出力CSVファイルのパス
            start_date: 予測開始日（Noneの場合は履歴の翌日から）
            future_days: 予測日数
            reserve_csv: 予約CSVファイルのパス
            reserve_date_col: 予約日付の列名
            reserve_count_col: 予約台数の列名
            reserve_fixed_col: 固定客の列名
            reserve_default_count: 予約のデフォルト件数
            reserve_default_sum: 予約のデフォルト合計
            reserve_default_fixed: 予約のデフォルト固定客比率
            **kwargs: その他のrun_inferenceパラメータ
            
        Returns:
            pd.DataFrame: 予測結果
            
        Raises:
            ImportError: serve_predict_model_v4_2_4がインポートできない
            RuntimeError: 予測実行に失敗
        """
        if _run_inference_impl is None:
            raise ImportError("serve_predict_model_v4_2_4.run_inference をインポートできませんでした")
        
        # 出力ディレクトリを作成
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # パラメータを文字列に変換（run_inferenceはCLI由来なので）
        bundle_str = str(self.model_bundle_path)
        res_walk_str = str(self.res_walk_csv) if self.res_walk_csv else None
        reserve_str = str(reserve_csv) if reserve_csv else None
        out_csv_str = str(output_csv_path)
        start_date_str = start_date.isoformat() if start_date else None
        
        try:
            logger.info(f"Running inference: bundle={bundle_str}, out={out_csv_str}")
            
            # 既存のrun_inference関数を呼び出し
            _run_inference_impl(
                bundle_path=bundle_str,
                res_walk_csv=res_walk_str,
                reserve_csv=reserve_str,
                reserve_date_col=reserve_date_col,
                reserve_count_col=reserve_count_col,
                reserve_fixed_col=reserve_fixed_col,
                future_days=future_days,
                start_date=start_date_str,
                end_date=None,
                out_csv=out_csv_str,
                reserve_default_count=reserve_default_count,
                reserve_default_sum=reserve_default_sum,
                reserve_default_fixed=reserve_default_fixed,
                prompt_reserve=False,
                manual_reserve=None,
                **kwargs,
            )
            
            # 生成されたCSVを読み込んで返却
            if not output_csv_path.exists():
                raise RuntimeError(f"Output CSV not generated: {output_csv_path}")
            
            result = pd.read_csv(output_csv_path)
            logger.info(f"✅ Prediction completed: {len(result)} rows")
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            raise RuntimeError(f"Prediction execution failed: {e}") from e
