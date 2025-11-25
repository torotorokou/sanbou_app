"""
Port: ISalesTreeQuery

売上ツリー分析のクエリ抽象インターフェース
"""
from typing import Protocol
from app.domain.sales_tree import (
    SummaryRequest, 
    SummaryRow, 
    DailySeriesRequest, 
    DailyPoint,
    PivotRequest,
    CursorPage,
    MetricEntry,
    ExportRequest
)
from app.domain.sales_tree_detail import (
    DetailLinesRequest,
    DetailLinesResponse
)


class ISalesTreeQuery(Protocol):
    """売上ツリー分析クエリのPort"""
    
    def fetch_summary(self, req: SummaryRequest) -> list[SummaryRow]:
        """
        サマリーデータ取得（営業ごとのTOP-N集計）
        
        Args:
            req: サマリー取得リクエスト
            
        Returns:
            list[SummaryRow]: 営業ごとのサマリー行
        """
        ...
    
    def fetch_daily_series(self, req: DailySeriesRequest) -> list[DailyPoint]:
        """
        日次推移データ取得
        
        Args:
            req: 日次推移取得リクエスト
            
        Returns:
            list[DailyPoint]: 日別データポイント
        """
        ...
    
    def fetch_pivot(self, req: PivotRequest) -> CursorPage:
        """
        Pivotデータ取得（詳細ドリルダウン）
        
        Args:
            req: Pivot取得リクエスト
            
        Returns:
            CursorPage: ページネーション結果
        """
        ...
    
    def export_csv(self, req: ExportRequest) -> bytes:
        """
        CSV Export
        
        Args:
            req: Export取得リクエスト
            
        Returns:
            bytes: CSV データ（UTF-8 BOM付き）
        """
        ...
    
    def fetch_detail_lines(self, req: DetailLinesRequest) -> DetailLinesResponse:
        """
        詳細明細行取得（SalesTree集計行クリック時の詳細表示用）
        
        最後の集計軸に応じて粒度を切り替える:
        - last_group_by が 'item' の場合:
            → mart.v_sales_tree_detail_base の明細行（GROUP BY なし）
        - それ以外の場合:
            → sales_date, slip_no で GROUP BY した伝票単位のサマリ
        
        Args:
            req: DetailLinesRequest（期間、集計軸、フィルタ条件）
            
        Returns:
            DetailLinesResponse: 詳細明細行（mode + rows + total_count）
        """
        ...
