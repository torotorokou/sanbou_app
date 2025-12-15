"""
Get Forecast Result UseCase

予測結果を取得するアプリケーションロジック。

設計方針:
- リポジトリから結果を取得
- 存在しない場合は適切なレスポンスを返す
- エラーハンドリングを含む
"""
import logging
from typing import Optional

from app.core.domain.forecast_result import ForecastResult, ForecastResultNotFound
from app.core.ports.forecast_result_port import ForecastResultRepositoryPort

logger = logging.getLogger(__name__)


class GetForecastResultUseCase:
    """
    予測結果取得UseCase
    
    責務:
    - モデルタイプに応じた予測結果の取得
    - 結果が存在しない場合の処理
    - エラーハンドリング
    
    Example:
        >>> repo = CsvForecastResultRepository()
        >>> usecase = GetForecastResultUseCase(repo)
        >>> result = usecase.get_daily()
        >>> if result:
        ...     print(f"Found {len(result.records)} predictions")
    """
    
    def __init__(self, repository: ForecastResultRepositoryPort):
        self.repository = repository
    
    def get_daily(self) -> Optional[ForecastResult]:
        """
        日次予測結果を取得
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        
        Raises:
            RuntimeError: 予測結果の取得に失敗
        """
        try:
            logger.info("Fetching daily forecast result")
            result = self.repository.get_daily_result()
            
            if result:
                logger.info(f"✅ Daily forecast found: {len(result.records)} records")
            else:
                logger.info("ℹ️ Daily forecast not found")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get daily forecast: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get daily forecast: {e}") from e
    
    def get_monthly(self) -> Optional[ForecastResult]:
        """
        月次予測結果を取得
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        """
        try:
            logger.info("Fetching monthly forecast result")
            result = self.repository.get_monthly_result()
            
            if result:
                logger.info(f"✅ Monthly forecast found: {len(result.records)} records")
            else:
                logger.info("ℹ️ Monthly forecast not found")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get monthly forecast: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get monthly forecast: {e}") from e
    
    def get_weekly(self) -> Optional[ForecastResult]:
        """
        週次予測結果を取得
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        """
        try:
            logger.info("Fetching weekly forecast result")
            result = self.repository.get_weekly_result()
            
            if result:
                logger.info(f"✅ Weekly forecast found: {len(result.records)} records")
            else:
                logger.info("ℹ️ Weekly forecast not found")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get weekly forecast: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get weekly forecast: {e}") from e
    
    def get_landing(self, day: int = 14) -> Optional[ForecastResult]:
        """
        月次着地予測結果を取得
        
        Args:
            day: 予測時点（14日または21日）
        
        Returns:
            ForecastResult: 予測結果（存在しない場合はNone）
        """
        try:
            logger.info(f"Fetching landing forecast result (day={day})")
            result = self.repository.get_landing_result(day=day)
            
            if result:
                logger.info(f"✅ Landing forecast found: {len(result.records)} records")
            else:
                logger.info(f"ℹ️ Landing forecast not found (day={day})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get landing forecast: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get landing forecast: {e}") from e
