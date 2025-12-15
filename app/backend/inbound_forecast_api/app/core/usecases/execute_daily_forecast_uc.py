"""
Execute Daily Forecast UseCase

日次予測を実行するアプリケーションロジック。
"""
from datetime import date
from typing import Optional

from app.core.ports.prediction_port import IPredictionExecutor


class ExecuteDailyForecastUseCase:
    """
    日次予測を実行する UseCase。
    
    責務:
    - 予測実行の手順を定義
    - エラーハンドリング
    - ログ記録（将来的に）
    """
    
    def __init__(self, prediction_executor: IPredictionExecutor):
        self.prediction_executor = prediction_executor
        
    def execute(self, target_date: Optional[date] = None) -> str:
        """
        日次予測を実行。
        
        Args:
            target_date: 予測対象日（Noneの場合は明日）
            
        Returns:
            生成されたCSVファイルのパス
            
        Raises:
            RuntimeError: 予測実行に失敗
        """
        # TODO: ログ記録
        # TODO: メトリクス記録
        
        csv_path = self.prediction_executor.execute_daily_forecast(target_date)
        
        # TODO: 結果の検証
        
        return csv_path
