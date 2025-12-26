"""
Sales Tree Master Router - Filter option endpoints
売上ツリー分析用フィルタ候補取得

エンドポイント:
  - GET /analytics/sales-tree/masters/reps: 営業フィルタ候補
  - GET /analytics/sales-tree/masters/customers: 顧客フィルタ候補
  - GET /analytics/sales-tree/masters/items: 品目フィルタ候補

Note: これは「マスタAPI」ではなく、SalesTree分析画面のプルダウンフィルタ用です。
      mart.v_sales_tree_detail_base から SELECT DISTINCT で動的に取得します。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import SQLAlchemyError

from app.config.di_providers import get_sales_tree_repo
from app.core.domain.sales_tree import CategoryKind
from app.infra.adapters.sales_tree.sales_tree_repository import SalesTreeRepository
from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.exceptions import InfrastructureError

logger = get_module_logger(__name__)
router = APIRouter()


@router.get("/masters/reps", summary="Get sales reps filter options for SalesTree analysis")
def get_sales_reps_master(
    category_kind: CategoryKind = Query("waste", description="カテゴリ種別: waste, valuable"),
    repo: SalesTreeRepository = Depends(get_sales_tree_repo),
):
    """
    【SalesTree分析専用】営業フィルタ候補取得

    NOTE: これは「営業マスタAPI」ではありません。
    mart.v_sales_tree_detail_base から SELECT DISTINCT で動的に営業候補を取得します。

    用途: SalesTree分析画面のプルダウンフィルタ用
    データソース: mart.v_sales_tree_detail_base（実売上明細ビュー）

    **Query Parameters:**
    - category_kind: カテゴリ種別（'waste'=廃棄物, 'valuable'=有価物）

    **Response Example:**
    ```json
    [
        {"rep_id": 1, "rep_name": "矢作"},
        {"rep_id": 2, "rep_name": "渡辺"}
    ]
    ```
    """
    try:
        logger.info(
            f"GET /analytics/sales-tree/masters/reps (SalesTree filter API) category_kind={category_kind}"
        )
        reps = repo.get_sales_reps(category_kind)
        logger.info(f"Successfully retrieved {len(reps)} sales reps for filter")
        return reps
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_sales_reps_master: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message="Database error while fetching sales reps",
            cause=e,
        )
    except Exception as e:
        # 予期しない例外の最後のキャッチ
        logger.error(f"Unexpected error in get_sales_reps_master: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Internal server error while fetching sales reps: {str(e)}",
            cause=e,
        )


@router.get("/masters/customers", summary="Get customer filter options for SalesTree analysis")
def get_customers_master(
    category_kind: CategoryKind = Query("waste", description="カテゴリ種別: waste, valuable"),
    repo: SalesTreeRepository = Depends(get_sales_tree_repo),
):
    """
    【SalesTree分析専用】顧客フィルタ候補取得

    NOTE: これは「顧客マスタAPI」ではありません。
    mart.v_sales_tree_detail_base から SELECT DISTINCT で動的に顧客候補を取得します。

    用途: SalesTree分析画面のプルダウンフィルタ用
    データソース: mart.v_sales_tree_detail_base（実売上明細ビュー）

    **Query Parameters:**
    - category_kind: カテゴリ種別（'waste'=廃棄物, 'valuable'=有価物）
    """
    try:
        logger.info(
            f"GET /analytics/sales-tree/masters/customers (SalesTree filter API) category_kind={category_kind}"
        )
        customers = repo.get_customers(category_kind)
        logger.info(f"Successfully retrieved {len(customers)} customers for filter")
        return customers
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_customers_master: {str(e)}", exc_info=True)
        raise InfrastructureError(message="Database error while fetching customers", cause=e)
    except Exception as e:
        # 予期しない例外の最後のキャッチ
        logger.error(f"Unexpected error in get_customers_master: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Internal server error while fetching customers: {str(e)}", cause=e
        )


@router.get("/masters/items", summary="Get item filter options for SalesTree analysis")
def get_items_master(
    category_kind: CategoryKind = Query("waste", description="カテゴリ種別: waste, valuable"),
    repo: SalesTreeRepository = Depends(get_sales_tree_repo),
):
    """
    【SalesTree分析専用】商品フィルタ候補取得

    NOTE: これは「商品マスタAPI」ではありません。
    mart.v_sales_tree_detail_base から SELECT DISTINCT で動的に商品候補を取得します。

    用途: SalesTree分析画面のプルダウンフィルタ用
    データソース: mart.v_sales_tree_detail_base（実売上明細ビュー）

    **Query Parameters:**
    - category_kind: カテゴリ種別（'waste'=廃棄物, 'valuable'=有価物）
    """
    try:
        logger.info(
            f"GET /analytics/sales-tree/masters/items (SalesTree filter API) category_kind={category_kind}"
        )
        items = repo.get_items(category_kind)
        logger.info(f"Successfully retrieved {len(items)} items for filter")
        return items
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_items_master: {str(e)}", exc_info=True)
        raise InfrastructureError(message="Database error while fetching items", cause=e)
    except Exception as e:
        # 予期しない例外の最後のキャッチ
        logger.error(f"Unexpected error in get_items_master: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Internal server error while fetching items: {str(e)}", cause=e
        )
