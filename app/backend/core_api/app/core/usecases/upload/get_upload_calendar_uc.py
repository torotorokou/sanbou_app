"""
Get Upload Calendar UseCase - アップロードカレンダー取得ユースケース

指定された年月のCSVアップロード履歴をカレンダー形式で取得します。
"""
import logging
from typing import List, Dict, Any

from app.core.ports.upload_status_port import IUploadStatusQuery
from backend_shared.application.logging import log_usecase_execution, create_log_context, get_module_logger

logger = get_module_logger(__name__)


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
        
        logger.info(
            "アップロードカレンダー取得開始",
            extra=create_log_context(operation="get_upload_calendar", year=year, month=month)
        )
        
        # データ取得（Port経由）
        items = self.query.get_upload_calendar(year, month)
        
        logger.info(
            "アップロードカレンダー取得成功",
            extra=create_log_context(operation="get_upload_calendar", items_count=len(items))
        )
        
        return items
