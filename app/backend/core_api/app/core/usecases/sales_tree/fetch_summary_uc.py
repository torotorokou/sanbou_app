"""
UseCase: FetchSalesTreeSummary

売上ツリーのサマリーデータ取得UseCase
"""

from app.core.domain.sales_tree import SummaryRequest, SummaryRow
from app.core.ports.sales_tree_port import ISalesTreeQuery
from backend_shared.application.logging import get_module_logger, log_usecase_execution

logger = get_module_logger(__name__)


class FetchSalesTreeSummaryUseCase:
    """
    売上ツリーサマリー取得UseCase

    営業ごとのTOP-N集計を取得
    """

    def __init__(self, query: ISalesTreeQuery):
        self._query = query

    @log_usecase_execution(usecase_name="FetchSalesTreeSummary", log_args=True)
    def execute(self, req: SummaryRequest) -> list[SummaryRow]:
        """
        サマリーデータを取得

        Args:
            req: サマリー取得リクエスト

        Returns:
            list[SummaryRow]: 営業ごとのサマリー行
        """
        return self._query.fetch_summary(req)
