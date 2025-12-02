"""
Get Upload Calendar UseCase

アップロードカレンダー表示用のデータ取得UseCase。
指定年月のアップロード済みCSVファイルの情報を集計します。

設計方針:
  - 複雑なSQL集計ロジックをPort&Adapter化
  - Router層からSQL実行を排除
"""
import logging
from typing import List, Dict, Any
from datetime import date
from calendar import monthrange

from app.core.ports.upload_status_port import IUploadCalendarQuery
from backend_shared.application.logging import create_log_context

logger = logging.getLogger(__name__)


class GetUploadCalendarDetailUseCase:
    """
    アップロードカレンダー取得UseCase
    
    指定年月の全アップロードファイルについて、
    データ日付、CSV種別、行数、upload_file_idを集計します。
    """

    def __init__(self, query: IUploadCalendarQuery):
        """
        Args:
            query: アップロードカレンダー取得Port実装
        """
        self.query = query

    def execute(self, year: int, month: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        指定年月のアップロードカレンダーデータを取得
        
        Args:
            year: 年（例: 2025）
            month: 月（1-12）
        
        Returns:
            {
                "items": [
                    {
                        "uploadFileId": <id>,
                        "date": "YYYY-MM-DD",
                        "csvKind": <kind>,
                        "rowCount": <count>
                    },
                    ...
                ]
            }
        """
        # 指定月の開始日・終了日を計算
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # Port経由でデータ取得
        items = self.query.fetch_upload_calendar(start_date, end_date)
        
        logger.info(
            "アップロードカレンダー詳細取得",
            extra=create_log_context(year=year, month=month, items_count=len(items))
        )
        return {"items": items}
