"""
UseCase: Get Inbound Daily Data

日次搬入量データ取得UseCase
"""
import logging
from datetime import date as date_type
from typing import List, Optional

from app.domain.inbound import InboundDailyRow, CumScope
from app.domain.ports.inbound_repository_port import IInboundQuery

logger = logging.getLogger(__name__)


class GetInboundDailyUseCase:
    """
    日次搬入量データ取得UseCase
    
    Port経由でデータを取得し、ビジネスロジックを適用
    """
    
    def __init__(self, query: IInboundQuery):
        self._query = query
    
    def execute(
        self,
        start: date_type,
        end: date_type,
        segment: Optional[str] = None,
        cum_scope: CumScope = "none"
    ) -> List[InboundDailyRow]:
        """
        日次搬入量データを取得
        
        Args:
            start: 開始日
            end: 終了日
            segment: セグメントフィルタ（オプション）
            cum_scope: 累積計算スコープ
            
        Returns:
            日次搬入量データのリスト
            
        Raises:
            ValueError: バリデーションエラー
        """
        # Validation
        if start > end:
            raise ValueError(f"start date ({start}) must be <= end date ({end})")
        
        # Fetch data via port
        data = self._query.fetch_daily(start, end, segment, cum_scope)
        
        logger.info(
            f"GetInboundDailyUseCase: fetched {len(data)} rows, "
            f"start={start}, end={end}, segment={segment}, cum_scope={cum_scope}"
        )
        
        return data
