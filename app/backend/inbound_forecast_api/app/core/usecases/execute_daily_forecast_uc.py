"""
Execute Daily Forecast UseCase

日次予測を実行するアプリケーションロジック。

設計方針:
- ドメインエンティティを使用した型安全な実装
- バリデーションはPydanticに委譲
- ビジネスロジックの明確化
"""
from app.core.domain.prediction import (
    DailyForecastRequest,
    PredictionOutput,
)
from app.core.ports.prediction_port import IPredictionExecutor


class ExecuteDailyForecastUseCase:
    """
    日次予測を実行する UseCase。
    
    責務:
    - 予測実行の手順を定義
    - リクエストのバリデーション（Pydanticによる）
    - エラーハンドリング
    - ログ記録（将来的に）
    
    Example:
        >>> uc = ExecuteDailyForecastUseCase(executor)
        >>> request = DailyForecastRequest(target_date=date(2025, 1, 22))
        >>> output = uc.execute(request)
        >>> print(output.csv_path)
    """
    
    def __init__(self, prediction_executor: IPredictionExecutor):
        self.prediction_executor = prediction_executor
        
    def execute(self, request: DailyForecastRequest) -> PredictionOutput:
        """
        日次予測を実行。
        
        Args:
            request: 予測リクエスト（DailyForecastRequest）
            
        Returns:
            PredictionOutput: 予測実行の結果（CSVパスと予測データ）
            
        Raises:
            ValidationError: リクエストのバリデーションエラー（Pydanticが自動発生）
            RuntimeError: 予測実行に失敗
        """
        # TODO: ログ記録
        # TODO: メトリクス記録
        
        # Executorに委譲（型安全）
        output = self.prediction_executor.execute_daily_forecast(request)
        
        # TODO: 結果の検証
        # - CSVファイルの存在確認
        # - 予測値の妥当性チェック（負の値がないか等）
        
        return output
