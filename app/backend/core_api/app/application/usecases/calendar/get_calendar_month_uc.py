"""
Get Calendar Month UseCase - 月次カレンダーデータ取得ユースケース

指定された年月の営業カレンダーデータを取得し、
営業日判定・祝日情報を提供します。
"""
import logging
from typing import List, Dict, Any

from app.domain.ports.calendar_port import ICalendarQuery

logger = logging.getLogger(__name__)


class GetCalendarMonthUseCase:
    """
    月次カレンダーデータ取得ユースケース
    
    責務:
      - 年月のバリデーション（範囲チェック）
      - カレンダーデータの取得（Port経由）
      - ログ記録
    """
    
    def __init__(self, query: ICalendarQuery):
        """
        Args:
            query: カレンダーデータ取得の抽象インターフェース
        """
        self.query = query
    
    def execute(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        指定された年月のカレンダーデータを取得
        
        Args:
            year: 年 (1900-2100)
            month: 月 (1-12)
            
        Returns:
            カレンダーデータのリスト
            
        Raises:
            ValueError: 年月の範囲外
            Exception: データベースエラー
        """
        # バリデーション
        if not (1900 <= year <= 2100):
            raise ValueError(f"Invalid year: {year} (must be 1900-2100)")
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month} (must be 1-12)")
        
        logger.info(f"Fetching calendar for {year}-{month:02d}")
        
        # データ取得（Port経由）
        data = self.query.get_month_calendar(year, month)
        
        logger.info(f"Successfully fetched calendar: {len(data)} days")
        
        return data
