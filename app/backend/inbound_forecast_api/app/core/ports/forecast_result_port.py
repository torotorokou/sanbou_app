"""
Forecast Result Repository Port

予測結果を取得するためのPort（抽象インターフェース）。

実装:
- CsvForecastResultRepository: CSVファイルから読み込み
- 将来的にはDBから取得する実装も可能
"""
from typing import Protocol, Optional
from app.core.domain.forecast_result import ForecastResult


class ForecastResultRepositoryPort(Protocol):
    """
    予測結果リポジトリの抽象インターフェース
    
    責務:
    - モデルタイプに応じた予測結果の取得
    - ファイルが存在しない場合の適切な処理
    
    Example:
        >>> repo = CsvForecastResultRepository()
        >>> result = repo.get_daily_result()
        >>> if result:
        ...     print(f"Found {len(result.records)} predictions")
    """
    
    def get_daily_result(self) -> Optional[ForecastResult]:
        """
        日次予測結果を取得
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        """
        ...
    
    def get_monthly_result(self) -> Optional[ForecastResult]:
        """
        月次予測結果を取得
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        """
        ...
    
    def get_weekly_result(self) -> Optional[ForecastResult]:
        """
        週次予測結果を取得
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        """
        ...
    
    def get_landing_result(self, day: int = 14) -> Optional[ForecastResult]:
        """
        月次着地予測結果を取得
        
        Args:
            day: 予測時点（14日または21日）
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        """
        ...
