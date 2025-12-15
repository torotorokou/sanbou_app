"""
Sales Tree Query Router - Summary, daily series, and pivot endpoints
売上ツリー分析のクエリエンドポイント

エンドポイント:
  - POST /analytics/sales-tree/summary: サマリーデータ取得
  - POST /analytics/sales-tree/daily-series: 日次推移データ取得
  - POST /analytics/sales-tree/pivot: Pivotデータ取得（詳細ドリルダウン）
"""
from fastapi import APIRouter, Depends

from backend_shared.application.logging import get_module_logger
from app.config.di_providers import (
    get_fetch_sales_tree_summary_uc,
    get_fetch_sales_tree_daily_series_uc,
    get_fetch_sales_tree_pivot_uc,
)
from app.core.usecases.sales_tree.fetch_summary_uc import FetchSalesTreeSummaryUseCase
from app.core.usecases.sales_tree.fetch_daily_series_uc import FetchSalesTreeDailySeriesUseCase
from app.core.usecases.sales_tree.fetch_pivot_uc import FetchSalesTreePivotUseCase
from app.core.domain.sales_tree.entities import (
    SummaryRequest,
    SummaryRow,
    DailySeriesRequest,
    DailyPoint,
    PivotRequest,
    CursorPage,
)
from backend_shared.core.domain.exceptions import InfrastructureError

logger = get_module_logger(__name__)
router = APIRouter()


@router.post("/summary", response_model=list[SummaryRow], response_model_by_alias=True, summary="Get sales tree summary")
def get_summary(
    req: SummaryRequest,
    uc: FetchSalesTreeSummaryUseCase = Depends(get_fetch_sales_tree_summary_uc),
):
    """
    売上ツリーサマリーデータ取得
    
    営業ごとに、指定軸（顧客/品目/日付）でTOP-N集計を返す
    
    **パラメータ:**
    - date_from: 集計開始日
    - date_to: 集計終了日
    - mode: 集計軸（customer, item, date）
    - rep_ids: 営業IDフィルタ（空=全営業）
    - filter_ids: 軸IDフィルタ（空=全データ）
    - top_n: TOP-N件数（0=全件）
    - sort_by: ソート項目（amount, qty, slip_count, unit_price, date, name）
    - order: ソート順（asc, desc）
    
    **使用例:**
    ```json
    {
        "date_from": "2025-10-01",
        "date_to": "2025-10-31",
        "mode": "customer",
        "rep_ids": [101, 102],
        "filter_ids": [],
        "top_n": 20,
        "sort_by": "amount",
        "order": "desc"
    }
    ```
    """
    try:
        logger.info(f"POST /analytics/sales-tree/summary: mode={req.mode}, date_from={req.date_from}, date_to={req.date_to}")
        
        result = uc.execute(req)
        
        logger.info(f"Successfully retrieved summary: {len(result)} reps")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_summary: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Internal server error while fetching summary: {str(e)}",
            cause=e
        )


@router.post("/daily-series", response_model=list[DailyPoint], response_model_by_alias=True, summary="Get daily series data")
def get_daily_series(
    req: DailySeriesRequest,
    uc: FetchSalesTreeDailySeriesUseCase = Depends(get_fetch_sales_tree_daily_series_uc),
):
    """
    日次推移データ取得
    
    指定条件（営業/顧客/品目）での日別推移を返す
    
    **パラメータ:**
    - date_from: 取得開始日
    - date_to: 取得終了日
    - rep_id: 営業IDフィルタ（省略可）
    - customer_id: 顧客IDフィルタ（省略可）
    - item_id: 品目IDフィルタ（省略可）
    
    **使用例:**
    ```json
    {
        "date_from": "2025-10-01",
        "date_to": "2025-10-31",
        "rep_id": 101
    }
    ```
    """
    try:
        logger.info(f"POST /analytics/sales-tree/daily-series: date_from={req.date_from}, date_to={req.date_to}")
        
        result = uc.execute(req)
        
        logger.info(f"Successfully retrieved daily series: {len(result)} points")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_daily_series: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Internal server error while fetching daily series: {str(e)}",
            cause=e
        )


@router.post("/pivot", response_model=CursorPage, response_model_by_alias=True, summary="Get pivot data for drill-down")
def get_pivot(
    req: PivotRequest,
    uc: FetchSalesTreePivotUseCase = Depends(get_fetch_sales_tree_pivot_uc),
):
    """
    Pivotデータ取得（詳細ドリルダウン）
    
    固定軸（baseAxis + baseId）に対して、別の軸（targetAxis）で展開
    
    **使用例:**
    顧客「泉土木」に対して、品目別の内訳を取得
    ```json
    {
        "date_from": "2025-10-01",
        "date_to": "2025-10-31",
        "base_axis": "customer",
        "base_id": "000014",
        "rep_ids": [1],
        "target_axis": "item",
        "top_n": 20,
        "sort_by": "amount",
        "order": "desc",
        "cursor": null
    }
    ```
    
    **ページネーション:**
    - レスポンスの`next_cursor`が非Nullの場合、次ページが存在
    - 次ページ取得時は、`cursor`パラメータに`next_cursor`の値を指定
    """
    try:
        logger.info(f"POST /analytics/sales-tree/pivot: base={req.base_axis}:{req.base_id}, target={req.target_axis}")
        
        result = uc.execute(req)
        
        logger.info(f"Successfully retrieved pivot: {len(result.rows)} rows")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_pivot: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Internal server error while fetching pivot: {str(e)}",
            cause=e
        )
