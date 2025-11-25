"""
UseCase: FetchSalesTreeDetailLines

売上ツリーの詳細明細行取得UseCase
"""
import logging
from app.domain.sales_tree_detail import DetailLinesRequest, DetailLinesResponse
from app.domain.ports.sales_tree_port import ISalesTreeQuery

logger = logging.getLogger(__name__)


class FetchSalesTreeDetailLinesUseCase:
    """
    売上ツリー詳細明細行取得UseCase
    
    集計行クリック時の詳細テーブル表示用データを取得
    最後の集計軸に応じて、明細行レベル or 伝票単位サマリを返す
    """
    
    def __init__(self, query: ISalesTreeQuery):
        self._query = query
    
    def execute(self, req: DetailLinesRequest) -> DetailLinesResponse:
        """
        詳細明細行を取得
        
        Args:
            req: 詳細明細行取得リクエスト
            
        Returns:
            DetailLinesResponse: 詳細明細行レスポンス（mode + rows + total_count）
        """
        try:
            logger.info(
                f"FetchSalesTreeDetailLinesUseCase: last_group_by={req.last_group_by}, "
                f"date_from={req.date_from}, date_to={req.date_to}, "
                f"rep_id={req.rep_id}, customer_id={req.customer_id}, item_id={req.item_id}"
            )
            return self._query.fetch_detail_lines(req)
        except Exception as e:
            logger.error(f"Error in FetchSalesTreeDetailLinesUseCase: {str(e)}", exc_info=True)
            raise
