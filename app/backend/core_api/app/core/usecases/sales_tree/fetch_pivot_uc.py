"""
UseCase: FetchSalesTreePivot

売上ツリーのPivotデータ取得UseCase（詳細ドリルダウン）
"""
import logging
from app.core.domain.sales_tree import PivotRequest, CursorPage
from app.core.ports.sales_tree_port import ISalesTreeQuery

logger = logging.getLogger(__name__)


class FetchSalesTreePivotUseCase:
    """
    売上ツリーPivot取得UseCase
    
    固定軸に対して別の軸で展開
    """
    
    def __init__(self, query: ISalesTreeQuery):
        self._query = query
    
    def execute(self, req: PivotRequest) -> CursorPage:
        """
        Pivotデータを取得
        
        Args:
            req: Pivot取得リクエスト
            
        Returns:
            CursorPage: ページネーション結果
        """
        try:
            logger.info(f"FetchSalesTreePivotUseCase: base={req.base_axis}:{req.base_id}, target={req.target_axis}")
            return self._query.fetch_pivot(req)
        except Exception as e:
            logger.error(f"Error in FetchSalesTreePivotUseCase: {str(e)}", exc_info=True)
            raise
