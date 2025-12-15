"""
UseCase: FetchSalesTreePivot

売上ツリーのPivotデータ取得UseCase（詳細ドリルダウン）
"""
import logging
from app.core.domain.sales_tree.entities import PivotRequest, CursorPage
from app.core.ports.sales_tree_port import ISalesTreeQuery
from backend_shared.application.logging import create_log_context, get_module_logger

logger = get_module_logger(__name__)


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
            logger.info(
                "FetchSalesTreePivot実行",
                extra=create_log_context(
                    operation="fetch_pivot",
                    base_axis=req.base_axis,
                    base_id=req.base_id,
                    target_axis=req.target_axis
                )
            )
            return self._query.fetch_pivot(req)
        except Exception as e:
            logger.error(
                "FetchSalesTreePivotエラー",
                extra=create_log_context(operation="fetch_pivot", error=str(e)),
                exc_info=True
            )
            raise
