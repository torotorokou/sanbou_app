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
