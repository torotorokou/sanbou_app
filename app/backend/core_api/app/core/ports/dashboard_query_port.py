"""
Port: IDashboardTargetQuery

Dashboard系のターゲット取得に必要な抽象インターフェース。
"""

from datetime import date as date_type
from typing import Any, Dict, Optional, Protocol


class IDashboardTargetQuery(Protocol):
    """ダッシュボードターゲット取得のPort"""

    def get_by_date_optimized(
        self, target_date: date_type, mode: str = "daily"
    ) -> Optional[Dict[str, Any]]:
        """
        指定日付のターゲットメトリクスを取得（最適化版）

        Args:
            target_date: 対象日付
            mode: "daily" または "monthly"

        Returns:
            Optional[Dict]: ターゲットメトリクス
        """
        ...
