"""
UseCase: BuildTargetCardUseCase

ダッシュボードのターゲットカード表示に必要なデータを取得・構築。

設計方針:
  - リポジトリ経由でデータを取得
  - キャッシュ制御もここで実施
  - 外部依存はPort経由
"""
import logging
from datetime import date as date_type
from typing import Optional, Dict, Any, Literal

from app.domain.ports.dashboard_query_port import IDashboardTargetQuery

logger = logging.getLogger(__name__)

Mode = Literal["daily", "monthly"]

# Optional TTL cache for repeated requests
try:
    from cachetools import TTLCache
    _CACHE: TTLCache = TTLCache(maxsize=256, ttl=60)  # 60 seconds TTL
    logger.info("TTL cache enabled for BuildTargetCardUseCase (60s, maxsize=256)")
except ImportError:
    _CACHE = None  # type: ignore
    logger.info("cachetools not installed, running without TTL cache")


class BuildTargetCardUseCase:
    """
    ターゲットカードデータ取得UseCase
    
    Features:
    - Port経由でリポジトリにアクセス
    - Optional TTL caching (60s) to reduce duplicate requests
    - Cache can be cleared manually via clear_cache()
    """
    
    def __init__(self, query: IDashboardTargetQuery):
        self._query = query

    def execute(
        self,
        requested_date: date_type,
        mode: Mode = "daily"
    ) -> Optional[Dict[str, Any]]:
        """
        ターゲットカードデータを取得
        
        Args:
            requested_date: 対象日付
            mode: "daily" または "monthly"
            
        Returns:
            Dict: ターゲット/実績データ、見つからない場合はNone
        """
        try:
            # Check cache first
            cache_key = (requested_date, mode)
            if _CACHE is not None and cache_key in _CACHE:
                logger.debug(f"Cache hit for {cache_key}")
                return _CACHE[cache_key]
            
            # Fetch using optimized repository method (single query)
            row = self._query.get_by_date_optimized(
                target_date=requested_date,
                mode=mode
            )
            
            if row and _CACHE is not None:
                _CACHE[cache_key] = row
                logger.debug(f"Cached result for {cache_key}")
            
            return row
            
        except Exception as e:
            logger.error(f"Error in execute for {requested_date}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def clear_cache() -> None:
        """Clear the TTL cache. Useful after CSV updates or data refreshes."""
        if _CACHE is not None:
            _CACHE.clear()
            logger.info("Target card cache cleared")
