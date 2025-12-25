"""
Ingest Repository Adapter

IngestPortの実装。PostgreSQL/SQLAlchemyを使用してデータ永続化。

設計方針:
  - ORM直接利用（将来的にテーブル定義が確定次第、完全実装）
  - トランザクション管理はSession委譲
"""

from datetime import date as date_type
from typing import Dict, List

from backend_shared.application.logging import create_log_context, get_module_logger
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)


class IngestRepository:
    """IngestPort実装（SQLAlchemy）"""

    def __init__(self, db: Session):
        self.db = db

    def upsert_actuals(self, rows: List[dict]) -> None:
        """
        実績データの登録/更新

        TODO: 完全実装には以下が必要:
          - テーブル定義の確定（ORM model）
          - INSERT ON CONFLICT UPDATE ロジック
          - バルクインサート最適化

        Args:
            rows: 実績データ行（辞書形式）

        Note:
            現状はログ出力のみ（スタブ実装）
        """
        logger.info(
            "upsert_actuals (stub)",
            extra=create_log_context(operation="upsert_actuals", rows_count=len(rows)),
        )
        # TODO: 実際のDB操作実装
        # 例: bulk_insert_mappings, INSERT ON CONFLICT 等

    def insert_reservation(self, date: date_type, trucks: int) -> dict:
        """
        トラック予約の登録

        TODO: 完全実装には以下が必要:
          - テーブル定義の確定（truck_reservations?）
          - UPSERT ロジック（日付が主キーの場合）
          - 返却値の設計

        Args:
            date: 予約日
            trucks: 台数

        Returns:
            登録結果

        Note:
            現状はログ出力のみ（スタブ実装）
        """
        logger.info(
            "insert_reservation (stub)",
            extra=create_log_context(
                operation="insert_reservation", date=str(date), trucks=trucks
            ),
        )
        # TODO: 実際のDB操作実装
        return {"date": date, "trucks": trucks}
