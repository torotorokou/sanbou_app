"""
Inbound repository port (abstract interface).
日次搬入量データ取得のポート定義
"""

from abc import ABC, abstractmethod
from datetime import date as date_type
from typing import List, Optional

from app.core.domain.inbound import CumScope, InboundDailyRow


class InboundRepository(ABC):
    """
    Inbound daily data repository interface.
    日次搬入量データの取得を抽象化したリポジトリインターフェース
    """

    @abstractmethod
    def fetch_daily(
        self,
        start: date_type,
        end: date_type,
        segment: Optional[str] = None,
        cum_scope: CumScope = "none",
    ) -> List[InboundDailyRow]:
        """
        Fetch daily inbound data with calendar continuity (zero-filled missing days).

        Args:
            start: 開始日（必須）
            end: 終了日（必須）
            segment: セグメントフィルタ（オプション）
            cum_scope: 累積計算スコープ（"range"|"month"|"week"|"none"）

        Returns:
            連続日・0埋め済み日次搬入量データのリスト

        Raises:
            ValueError: start > end, または範囲が365日を超える場合
        """
        pass
