"""
UseCase: ExportSalesTreeCSV

売上ツリーのCSV Export UseCase
"""
import logging
from app.core.domain.sales_tree import ExportRequest
from app.core.ports.sales_tree_port import ISalesTreeQuery
from backend_shared.application.logging import create_log_context, get_module_logger

logger = get_module_logger(__name__)


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
            logger.info(
                "ExportSalesTreeCSV実行",
                extra=create_log_context(
                    operation="export_csv",
                    mode=req.mode,
                    date_from=str(req.date_from),
                    date_to=str(req.date_to)
                )
            )
            return self._query.export_csv(req)
        except Exception as e:
            logger.error(
                "ExportSalesTreeCSVエラー",
                extra=create_log_context(operation="export_csv", error=str(e)),
                exc_info=True
            )
            raise
