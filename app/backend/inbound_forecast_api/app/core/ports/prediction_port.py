"""
Prediction Execution Port

予測実行の抽象インターフェース。

設計方針:
- ドメインエンティティを使用した型安全なインターフェース
- 実装の詳細（subprocess, ライブラリ等）はAdapterに隠蔽
"""
from typing import Protocol

from app.core.domain.prediction import (
    DailyForecastRequest,
    PredictionOutput,
)


class IPredictionExecutor(Protocol):
    """
    予測スクリプトを実行するためのPort。
    
    Implementation例:
    - ScriptBasedPredictionExecutor: 既存のPythonスクリプトを subprocess で実行
    - DirectPredictionExecutor: スクリプトをライブラリ化して直接呼び出し
    - MockPredictionExecutor: テスト用のモック実装
    
    Example:
        >>> executor = ScriptBasedPredictionExecutor(scripts_dir=Path("/backend/scripts"))
        >>> request = DailyForecastRequest(target_date=date(2025, 1, 22))
        >>> output = executor.execute_daily_forecast(request)
        >>> print(output.csv_path)
        /backend/output/tplus1_pred_20251215_142253.csv
    """
    
    def execute_daily_forecast(self, request: DailyForecastRequest) -> PredictionOutput:
        """
        日次予測を実行。
        
        Args:
            request: 予測リクエスト（DailyForecastRequest）
            
        Returns:
            PredictionOutput: 予測実行の結果
                - csv_path: 生成されたCSVファイルのパス
                - predictions: 予測結果のリスト（オプション）
            
        Raises:
            FileNotFoundError: 必要なファイル（スクリプト、モデル等）が見つからない
            RuntimeError: 予測実行に失敗
            ValidationError: リクエストのバリデーションエラー
        """
        ...
