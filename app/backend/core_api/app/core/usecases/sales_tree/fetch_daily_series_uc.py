"""
UseCase: FetchSalesTreeDailySeries

売上ツリーの日次推移データ取得UseCase
"""
import logging
from backend_shared.application.logging import log_usecase_execution
from app.core.domain.sales_tree import DailySeriesRequest, DailyPoint
from app.core.ports.sales_tree_port import ISalesTreeQuery

logger = logging.getLogger(__name__)


class FetchSalesTreeDailySeriesUseCase:
    """
    売上ツリー日次推移取得UseCase
    
    指定条件での日別推移を取得
    """
    
    def __init__(self, query: ISalesTreeQuery):
        self._query = query
    
    @log_usecase_execution(usecase_name="FetchSalesTreeDailySeries", log_args=True)
    def execute(self, req: DailySeriesRequest) -> list[DailyPoint]:
        """
        日次推移データを取得
        
        Args:
            req: 日次推移取得リクエスト
            
        Returns:
            list[DailyPoint]: 日別データポイント
        """
        return self._query.fetch_daily_series(req)
