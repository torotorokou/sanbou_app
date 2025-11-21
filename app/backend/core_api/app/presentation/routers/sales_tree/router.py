"""
Sales Tree Router - 売上ツリー分析APIエンドポイント

売上ツリー画面で表示するサマリーデータと日次推移データを提供

機能:
  - サマリーデータ取得（営業ごとのTOP-N集計）
  - 日次推移データ取得
  - Pivotデータ取得（詳細ドリルダウン）
  - CSV Export

設計方針:
  - RouterはHTTP I/Oのみを担当（ビジネスロジックはUseCaseに委譲）
  - DI経由でUseCaseを取得（テスタビリティ向上）
  - エラーハンドリングを一元化
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
import logging

from app.config.di_providers import (
    get_fetch_sales_tree_summary_uc,
    get_fetch_sales_tree_daily_series_uc,
    get_fetch_sales_tree_pivot_uc,
    get_export_sales_tree_csv_uc,
    get_sales_tree_repo
)
from app.application.usecases.sales_tree.fetch_summary_uc import FetchSalesTreeSummaryUseCase
from app.application.usecases.sales_tree.fetch_daily_series_uc import FetchSalesTreeDailySeriesUseCase
from app.application.usecases.sales_tree.fetch_pivot_uc import FetchSalesTreePivotUseCase
from app.application.usecases.sales_tree.export_csv_uc import ExportSalesTreeCSVUseCase
from app.infra.adapters.sales_tree.sales_tree_repository import SalesTreeRepository
from app.domain.sales_tree import (
    SummaryRequest,
    SummaryRow,
    DailySeriesRequest,
    DailyPoint,
    PivotRequest,
    CursorPage,
    ExportRequest
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics/sales-tree", tags=["sales-tree"])


@router.post("/summary", response_model=list[SummaryRow], summary="Get sales tree summary")
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
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching summary: {str(e)}"
        )


@router.post("/daily-series", response_model=list[DailyPoint], summary="Get daily series data")
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
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching daily series: {str(e)}"
        )


@router.post("/pivot", response_model=CursorPage, summary="Get pivot data for drill-down")
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
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching pivot: {str(e)}"
        )


@router.post("/export", summary="Export sales tree data as CSV")
def export_csv(
    req: ExportRequest,
    uc: ExportSalesTreeCSVUseCase = Depends(get_export_sales_tree_csv_uc),
):
    """
    売上ツリーデータをCSV出力
    
    指定条件でサマリーデータをCSV形式で出力
    
    **パラメータ:**
    - date_from: 集計開始日
    - date_to: 集計終了日
    - mode: 集計軸（customer, item, date）
    - rep_ids: 営業IDフィルタ（空=全営業）
    - filter_ids: 軸IDフィルタ（空=全データ）
    - sort_by: ソート項目（amount, qty, slip_count, unit_price, date, name）
    - order: ソート順（asc, desc）
    
    **使用例:**
    ```json
    {
        "date_from": "2025-10-01",
        "date_to": "2025-10-31",
        "mode": "customer",
        "rep_ids": [1, 2],
        "filter_ids": [],
        "sort_by": "amount",
        "order": "desc"
    }
    ```
    """
    try:
        logger.info(f"POST /analytics/sales-tree/export: mode={req.mode}, date_from={req.date_from}, date_to={req.date_to}")
        
        csv_bytes = uc.execute(req)
        
        # ファイル名生成
        filename = f"sales_tree_{req.mode}_{req.date_from}_{req.date_to}.csv"
        
        logger.info(f"Successfully generated CSV: {filename}")
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in export_csv: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while exporting CSV: {str(e)}"
        )


@router.get("/masters/reps", summary="Get sales reps master data")
def get_sales_reps_master(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo),
):
    """
    営業マスタデータ取得
    
    sandbox.v_sales_tree_daily から重複を除いた営業一覧を返す
    
    **Response Example:**
    ```json
    [
        {"rep_id": 1, "rep_name": "矢作"},
        {"rep_id": 2, "rep_name": "渡辺"}
    ]
    ```
    """
    try:
        logger.info("GET /analytics/sales-tree/masters/reps")
        reps = repo.get_sales_reps()
        logger.info(f"Successfully retrieved {len(reps)} sales reps")
        return reps
    except Exception as e:
        logger.error(f"Error in get_sales_reps_master: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching sales reps: {str(e)}"
        )


@router.get("/masters/customers", summary="Get customers master data")
def get_customers_master(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo),
):
    """
    顧客マスタデータ取得
    
    sandbox.v_sales_tree_daily から重複を除いた顧客一覧を返す
    """
    try:
        logger.info("GET /analytics/sales-tree/masters/customers")
        customers = repo.get_customers()
        logger.info(f"Successfully retrieved {len(customers)} customers")
        return customers
    except Exception as e:
        logger.error(f"Error in get_customers_master: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching customers: {str(e)}"
        )


@router.get("/masters/items", summary="Get items master data")
def get_items_master(
    repo: SalesTreeRepository = Depends(get_sales_tree_repo),
):
    """
    品目マスタデータ取得
    
    sandbox.v_sales_tree_daily から重複を除いた品目一覧を返す
    """
    try:
        logger.info("GET /analytics/sales-tree/masters/items")
        items = repo.get_items()
        logger.info(f"Successfully retrieved {len(items)} items")
        return items
    except Exception as e:
        logger.error(f"Error in get_items_master: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching items: {str(e)}"
        )
