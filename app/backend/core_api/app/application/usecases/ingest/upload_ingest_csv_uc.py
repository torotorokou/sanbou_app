"""
Upload Ingest CSV UseCase

CSVアップロード処理をPort&Adapter化。
将来的にバリデーション・フォーマット処理を統合予定。

設計方針:
  - Port経由でDB操作を抽象化
  - backend_sharedのバリデーター統合を見据えた設計
  - 現時点はスタブ実装（TODO: 要件定義後に完全実装）
"""
from typing import List, Dict, Any

from app.domain.ports.ingest_port import IngestPort


class UploadIngestCsvUseCase:
    """
    CSVアップロード UseCase
    
    将来的な拡張予定:
      - backend_shared.usecases.csv_validator との統合
      - backend_shared.usecases.csv_formatter との統合
      - カラム仕様のYAML定義化
    """

    def __init__(self, ingest_repo: IngestPort):
        """
        Args:
            ingest_repo: データ永続化Port実装
        """
        self.ingest_repo = ingest_repo

    def execute(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        CSVデータをDB保存
        
        処理フロー:
          1. バリデーション（TODO: 要件定義後）
          2. フォーマット（TODO: 要件定義後）
          3. DB保存（Port経由）
        
        Args:
            rows: CSVから読み込んだ行データ（辞書形式）
        
        Returns:
            処理結果（成功/失敗、処理行数等）
        
        Note:
            現状はスタブ実装。完全実装には以下が必要:
            - CSVカラム仕様の明確化
            - 必須カラムの定義
            - 日付・数値のパース処理
            - エラーハンドリング戦略
        """
        # TODO: バリデーション実装
        # TODO: フォーマット処理実装
        
        # DB保存（Port経由）
        self.ingest_repo.upsert_actuals(rows)

        return {
            "success": True,
            "rows_processed": len(rows),
            "message": "CSV upload completed (Port&Adapter pattern)",
        }
