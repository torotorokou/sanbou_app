"""
Sales Tree Export Router - CSV export endpoint
売上ツリーデータのCSV出力

エンドポイント:
  - POST /analytics/sales-tree/export: CSV出力
"""
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.config.di_providers import get_export_sales_tree_csv_uc
from app.application.usecases.sales_tree.export_csv_uc import ExportSalesTreeCSVUseCase
from app.domain.sales_tree import ExportRequest
from app.shared.exceptions import InfrastructureError

logger = logging.getLogger(__name__)
router = APIRouter()


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
        raise InfrastructureError(
            message=f"Internal server error while exporting CSV: {str(e)}",
            cause=e
        )
