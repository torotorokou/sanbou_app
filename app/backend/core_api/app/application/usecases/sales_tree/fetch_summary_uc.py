"""
UseCase: FetchSalesTreeSummary

売上ツリーのサマリーデータ取得UseCase
"""
import logging
from app.domain.sales_tree import SummaryRequest, SummaryRow
from app.domain.ports.sales_tree_port import ISalesTreeQuery

logger = logging.getLogger(__name__)


class FetchSalesTreeSummaryUseCase:
    """
    売上ツリーサマリー取得UseCase
    
    営業ごとのTOP-N集計を取得
    """
    
    def __init__(self, query: ISalesTreeQuery):
        self._query = query
    
    def execute(self, req: SummaryRequest) -> list[SummaryRow]:
        """
        サマリーデータを取得
        
        Args:
            req: サマリー取得リクエスト
            
        Returns:
            list[SummaryRow]: 営業ごとのサマリー行
        """
        try:
            logger.info(f"FetchSalesTreeSummaryUseCase: mode={req.mode}, date_from={req.date_from}, date_to={req.date_to}")
            return self._query.fetch_summary(req)
        except Exception as e:
            logger.error(f"Error in FetchSalesTreeSummaryUseCase: {str(e)}", exc_info=True)
            raise
