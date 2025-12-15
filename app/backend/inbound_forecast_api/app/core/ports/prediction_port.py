"""
Prediction Execution Port

予測実行の抽象インターフェース。
"""
from typing import Protocol, Optional
from datetime import date


class IPredictionExecutor(Protocol):
    """
    予測スクリプトを実行するためのPort。
    
    Implementation例:
    - ScriptBasedPredictionExecutor: 既存のPythonスクリプトを subprocess で実行
    - DirectPredictionExecutor: スクリプトをライブラリ化して直接呼び出し
    """
    
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
        ...
