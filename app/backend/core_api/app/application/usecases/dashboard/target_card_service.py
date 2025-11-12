"""
Target Card Service: Business logic for target card data.
Optimized with single-query repository calls and optional TTL caching.

DEPRECATED: このServiceは非推奨です。
  - 代わりに app/application/usecases/dashboard/build_target_card_uc.py の BuildTargetCardUseCase を使用してください
  - Router層では app/config/di_providers.py の get_build_target_card_uc() を Depends で注入してください
  - UseCaseパターンに移行することで、ビジネスロジックの集約とテスタビリティが向上します
"""
from datetime import date as date_type, timedelta
from typing import Optional, Dict, Any, Literal
import logging

from app.repositories.dashboard_target_repo import DashboardTargetRepository

logger = logging.getLogger(__name__)

Mode = Literal["daily", "monthly"]

# Optional TTL cache for repeated requests
try:
    from cachetools import TTLCache
    _CACHE: TTLCache = TTLCache(maxsize=256, ttl=60)  # 60 seconds TTL
    logger.info("TTL cache enabled for TargetCardService (60s, maxsize=256)")
except ImportError:
    _CACHE = None  # type: ignore
    logger.info("cachetools not installed, running without TTL cache")


class TargetCardService:
    """
    Service for fetching target card data with optimized single-query approach.
    
    Features:
    - Uses repository's optimized single-query method (anchor + mask in one SQL)
    - Optional TTL caching (60s) to reduce duplicate requests
    - Cache can be cleared manually via clear_cache()
    """
    
    def __init__(self, repo: DashboardTargetRepository):
        self._repo = repo

    def get_by_date(self, requested_date: date_type, mode: Mode = "daily") -> Optional[Dict[str, Any]]:
        """
        Get target card data using optimized repository method.
        
        Args:
            requested_date: The date requested (typically YYYY-MM-01 for monthly view)
            mode: "daily" for day-specific data, "monthly" for month-level data with day/week masking
            
        Returns:
            Dict with target/actual data, or None if no data found
        """
        try:
            # Check cache first
            cache_key = (requested_date, mode)
            if _CACHE is not None and cache_key in _CACHE:
                logger.debug(f"Cache hit for {cache_key}")
                return _CACHE[cache_key]
            
            # Fetch using optimized repository method (single query)
            row = self._repo.get_by_date_optimized(requested_date, mode)
            
            if row and _CACHE is not None:
                _CACHE[cache_key] = row
                logger.debug(f"Cached result for {cache_key}")
            
            return row
            
        except Exception as e:
            logger.error(f"Error in get_by_date for {requested_date}: {str(e)}", exc_info=True)
            raise

    def clear_cache(self) -> None:
        """Clear the TTL cache. Useful after CSV updates or data refreshes."""
        if _CACHE is not None:
            _CACHE.clear()
            logger.info("Target card cache cleared")

