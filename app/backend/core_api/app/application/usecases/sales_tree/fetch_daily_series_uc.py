"""
UseCase: FetchSalesTreeDailySeries

売上ツリーの日次推移データ取得UseCase
"""
import logging
from app.domain.sales_tree import DailySeriesRequest, DailyPoint
from app.domain.ports.sales_tree_port import ISalesTreeQuery

logger = logging.getLogger(__name__)


class FetchSalesTreeDailySeriesUseCase:
    """
    売上ツリー日次推移取得UseCase
    
    指定条件での日別推移を取得
    """
    
    def __init__(self, query: ISalesTreeQuery):
        self._query = query
    
    def execute(self, req: DailySeriesRequest) -> list[DailyPoint]:
        """
        日次推移データを取得
        
        Args:
            req: 日次推移取得リクエスト
            
        Returns:
            list[DailyPoint]: 日別データポイント
        """
        try:
            logger.info(f"FetchSalesTreeDailySeriesUseCase: date_from={req.date_from}, date_to={req.date_to}")
            return self._query.fetch_daily_series(req)
        except Exception as e:
            logger.error(f"Error in FetchSalesTreeDailySeriesUseCase: {str(e)}", exc_info=True)
            raise
