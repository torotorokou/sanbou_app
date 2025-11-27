"""
Upload Calendar Query Adapter

アップロードカレンダー表示用のSQL集計ロジックを実装。
複雑なUNION ALLによる集計クエリをカプセル化します。
"""
import logging
from typing import List, Dict, Any
from datetime import date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class UploadCalendarQueryAdapter:
    """アップロードカレンダー取得Adapter（IUploadCalendarQuery実装）"""

    def __init__(self, db: Session):
        self.db = db

    def fetch_upload_calendar(
        self, start_date: date_type, end_date: date_type
    ) -> List[Dict[str, Any]]:
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
        sql = text("""
            WITH upload_data AS (
                -- 将軍速報版 受入
                SELECT 
                    uf.id AS upload_file_id,
                    s.slip_date AS data_date,
                    'shogun_flash_receive'::text AS csv_kind,
                    COUNT(*) AS row_count
                FROM log.upload_file uf
                JOIN stg.shogun_flash_receive s ON s.upload_file_id = uf.id
                WHERE uf.is_deleted = false
                  AND s.is_deleted = false
                  AND s.slip_date IS NOT NULL
                  AND s.slip_date >= :start_date
                  AND s.slip_date <= :end_date
                GROUP BY uf.id, s.slip_date
                
                UNION ALL
                
                -- 将軍速報版 ヤード
                SELECT 
                    uf.id AS upload_file_id,
                    s.slip_date AS data_date,
                    'shogun_flash_yard'::text AS csv_kind,
                    COUNT(*) AS row_count
                FROM log.upload_file uf
                JOIN stg.shogun_flash_yard s ON s.upload_file_id = uf.id
                WHERE uf.is_deleted = false
                  AND s.is_deleted = false
                  AND s.slip_date IS NOT NULL
                  AND s.slip_date >= :start_date
                  AND s.slip_date <= :end_date
                GROUP BY uf.id, s.slip_date
                
                UNION ALL
                
                -- 将軍速報版 出荷
                SELECT 
                    uf.id AS upload_file_id,
                    s.slip_date AS data_date,
                    'shogun_flash_shipment'::text AS csv_kind,
                    COUNT(*) AS row_count
                FROM log.upload_file uf
                JOIN stg.shogun_flash_shipment s ON s.upload_file_id = uf.id
                WHERE uf.is_deleted = false
                  AND s.is_deleted = false
                  AND s.slip_date IS NOT NULL
                  AND s.slip_date >= :start_date
                  AND s.slip_date <= :end_date
                GROUP BY uf.id, s.slip_date
                
                UNION ALL
                
                -- 将軍最終版 受入
                SELECT 
                    uf.id AS upload_file_id,
                    s.slip_date AS data_date,
                    'shogun_final_receive'::text AS csv_kind,
                    COUNT(*) AS row_count
                FROM log.upload_file uf
                JOIN stg.shogun_final_receive s ON s.upload_file_id = uf.id
                WHERE uf.is_deleted = false
                  AND s.is_deleted = false
                  AND s.slip_date IS NOT NULL
                  AND s.slip_date >= :start_date
                  AND s.slip_date <= :end_date
                GROUP BY uf.id, s.slip_date
                
                UNION ALL
                
                -- 将軍最終版 出荷
                SELECT 
                    uf.id AS upload_file_id,
                    s.slip_date AS data_date,
                    'shogun_final_shipment'::text AS csv_kind,
                    COUNT(*) AS row_count
                FROM log.upload_file uf
                JOIN stg.shogun_final_shipment s ON s.upload_file_id = uf.id
                WHERE uf.is_deleted = false
                  AND s.is_deleted = false
                  AND s.slip_date IS NOT NULL
                  AND s.slip_date >= :start_date
                  AND s.slip_date <= :end_date
                GROUP BY uf.id, s.slip_date
                
                UNION ALL
                
                -- 将軍最終版 ヤード
                SELECT 
                    uf.id AS upload_file_id,
                    s.slip_date AS data_date,
                    'shogun_final_yard'::text AS csv_kind,
                    COUNT(*) AS row_count
                FROM log.upload_file uf
                JOIN stg.shogun_final_yard s ON s.upload_file_id = uf.id
                WHERE uf.is_deleted = false
                  AND s.is_deleted = false
                  AND s.slip_date IS NOT NULL
                  AND s.slip_date >= :start_date
                  AND s.slip_date <= :end_date
                GROUP BY uf.id, s.slip_date
            )
            SELECT 
                upload_file_id,
                data_date,
                csv_kind,
                row_count
            FROM upload_data
            ORDER BY data_date, csv_kind, upload_file_id
        """)

        result = self.db.execute(sql, {"start_date": start_date, "end_date": end_date})
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
