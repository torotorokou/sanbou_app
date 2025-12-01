"""
UseCase: ExportSalesTreeCSV

売上ツリーのCSV Export UseCase
"""
import logging
from app.core.domain.sales_tree import ExportRequest
from app.core.ports.sales_tree_port import ISalesTreeQuery

logger = logging.getLogger(__name__)


class ExportSalesTreeCSVUseCase:
    """
    売上ツリーCSV Export UseCase
    
    指定条件でCSVファイルを生成
    """
    
    def __init__(self, query: ISalesTreeQuery):
        self._query = query
    
    def execute(self, req: ExportRequest) -> bytes:
        """
        CSVデータを生成
        
        Args:
            req: Export取得リクエスト
            
        Returns:
            bytes: CSV データ（UTF-8 BOM付き）
        """
        try:
            logger.info(f"ExportSalesTreeCSVUseCase: mode={req.mode}, date_from={req.date_from}, date_to={req.date_to}")
            return self._query.export_csv(req)
        except Exception as e:
            logger.error(f"Error in ExportSalesTreeCSVUseCase: {str(e)}", exc_info=True)
            raise
