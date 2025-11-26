"""
Get Upload Calendar UseCase - アップロードカレンダー取得ユースケース

指定された年月のCSVアップロード履歴をカレンダー形式で取得します。
"""
import logging
from typing import List, Dict, Any

from app.domain.ports.upload_status_port import IUploadStatusQuery
from app.shared.logging_utils import log_usecase_execution

logger = logging.getLogger(__name__)


class GetUploadCalendarUseCase:
    """
    アップロードカレンダー取得ユースケース
    
    責務:
      - 年月のバリデーション
      - カレンダーデータの取得（Port経由）
      - ログ記録
    """
    
    def __init__(self, query: IUploadStatusQuery):
        """
        Args:
            query: アップロードステータス取得の抽象インターフェース
        """
        self.query = query
    
    @log_usecase_execution(usecase_name="GetUploadCalendar", log_result=True)
    def execute(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        指定月のアップロードカレンダーデータを取得
        
        Args:
            year: 年
            month: 月 (1-12)
            
        Returns:
            カレンダーアイテムのリスト
            
        Raises:
            ValueError: 年月が不正な場合
            Exception: データベースエラー
        """
        # バリデーション
        if not (1900 <= year <= 2100):
            raise ValueError(f"Invalid year: {year} (must be 1900-2100)")
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month} (must be 1-12)")
        
        logger.info(f"Fetching upload calendar for {year}-{month:02d}")
        
        # データ取得（Port経由）
        items = self.query.get_upload_calendar(year, month)
        
        logger.info(f"Successfully fetched upload calendar: {len(items)} items")
        
        return items
