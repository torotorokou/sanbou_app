"""
Upload Calendar Query Adapter

アップロードカレンダー表示用のSQL集計ロジックを実装。
複雑なUNION ALLによる集計クエリをカプセル化します。
"""

from datetime import date as date_type
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infra.db.sql_loader import load_sql
from backend_shared.application.logging import get_module_logger
from backend_shared.db.names import (
    SCHEMA_LOG,
    SCHEMA_STG,
    T_UPLOAD_FILE,
    V_ACTIVE_SHOGUN_FINAL_RECEIVE,
    V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
    V_ACTIVE_SHOGUN_FINAL_YARD,
    V_ACTIVE_SHOGUN_FLASH_RECEIVE,
    V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
    V_ACTIVE_SHOGUN_FLASH_YARD,
)

logger = get_module_logger(__name__)


class UploadCalendarQueryAdapter:
    """アップロードカレンダー取得Adapter（IUploadCalendarQuery実装）"""

    def __init__(self, db: Session):
        self.db = db
        # Pre-load SQL with table/schema name substitution
        template = load_sql("upload/upload_calendar__fetch_upload_calendar.sql")
        self._fetch_upload_calendar_sql = text(
            template.format(
                schema_log=SCHEMA_LOG,
                schema_stg=SCHEMA_STG,
                t_upload_file=T_UPLOAD_FILE,
                v_active_shogun_flash_receive=V_ACTIVE_SHOGUN_FLASH_RECEIVE,
                v_active_shogun_flash_yard=V_ACTIVE_SHOGUN_FLASH_YARD,
                v_active_shogun_flash_shipment=V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
                v_active_shogun_final_receive=V_ACTIVE_SHOGUN_FINAL_RECEIVE,
                v_active_shogun_final_shipment=V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
                v_active_shogun_final_yard=V_ACTIVE_SHOGUN_FINAL_YARD,
            )
        )

    def fetch_upload_calendar(
        self, start_date: date_type, end_date: date_type
    ) -> list[dict[str, Any]]:
        """
        指定期間のアップロードカレンダーデータを集計

        全CSV種別（flash/final × receive/yard/shipment）のデータを
        UNION ALL で集計し、日付・種別・行数を返します。

        Args:
            start_date: 開始日
            end_date: 終了日

        Returns:
            カレンダーアイテムのリスト
        """
        # SQL は外部ファイルから読み込み済み（__init__で定数置換済み）
        result = self.db.execute(
            self._fetch_upload_calendar_sql,
            {"start_date": start_date, "end_date": end_date},
        )
        rows = result.fetchall()

        return [
            {
                "uploadFileId": row[0],
                "date": row[1].strftime("%Y-%m-%d"),
                "csvKind": row[2],
                "rowCount": row[3],
            }
            for row in rows
        ]
