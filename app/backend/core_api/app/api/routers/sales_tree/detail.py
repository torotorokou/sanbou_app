"""
Sales Tree Detail Router - Detail lines endpoint
売上ツリー詳細明細行取得

エンドポイント:
  - POST /analytics/sales-tree/detail-lines: 詳細明細行取得
"""

from fastapi import APIRouter, Depends

from app.config.di_providers import get_fetch_sales_tree_detail_lines_uc
from app.core.domain.sales_tree_detail import DetailLinesRequest, DetailLinesResponse
from app.core.usecases.sales_tree.fetch_detail_lines_uc import (
    FetchSalesTreeDetailLinesUseCase,
)
from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.exceptions import InfrastructureError

logger = get_module_logger(__name__)
router = APIRouter()


@router.post(
    "/detail-lines",
    response_model=DetailLinesResponse,
    response_model_by_alias=True,
    summary="Get detail lines for clicked pivot row",
)
def get_detail_lines(
    req: DetailLinesRequest,
    uc: FetchSalesTreeDetailLinesUseCase = Depends(
        get_fetch_sales_tree_detail_lines_uc
    ),
):
    """
    売上ツリー詳細明細行取得

    集計行クリック時の詳細テーブル表示用データを返す
    最後の集計軸に応じて、明細行レベル or 伝票単位サマリを返す

    **パラメータ:**
    - date_from: 集計開始日
    - date_to: 集計終了日
    - last_group_by: 最後の集計軸（rep, customer, date, item）
    - category_kind: カテゴリ種別（waste, valuable）
    - rep_id: 営業IDフィルタ（オプション）
    - customer_id: 顧客IDフィルタ（オプション）
    - item_id: 品目IDフィルタ（オプション）
    - date_value: 日付フィルタ（オプション）

    **使用例 (品名明細):**
    ```json
    {
        "date_from": "2025-10-01",
        "date_to": "2025-10-31",
        "last_group_by": "item",
        "category_kind": "waste",
        "rep_id": 1,
        "customer_id": "C001",
        "item_id": 501
    }
    ```

    **使用例 (伝票単位サマリ):**
    ```json
    {
        "date_from": "2025-10-01",
        "date_to": "2025-10-31",
        "last_group_by": "customer",
        "category_kind": "waste",
        "rep_id": 1,
        "customer_id": "C001"
    }
    ```
    """
    try:
        logger.info(
            f"POST /analytics/sales-tree/detail-lines: last_group_by={req.last_group_by}, "
            f"date_from={req.date_from}, date_to={req.date_to}"
        )

        result = uc.execute(req)

        logger.info(
            f"Successfully retrieved detail lines: {result.total_count} rows (mode={result.mode})"
        )
        return result

    except Exception as e:
        logger.error(f"Error in get_detail_lines: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Internal server error while fetching detail lines: {str(e)}",
            cause=e,
        )
