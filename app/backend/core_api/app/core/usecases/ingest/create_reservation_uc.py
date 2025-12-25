"""
Create Reservation UseCase

トラック予約の作成/更新をPort&Adapter化。

設計方針:
  - Port経由でDB操作を抽象化
  - ビジネスルールの明確化（将来的に拡張）
"""

from datetime import datetime

from app.core.domain.models import ReservationCreate, ReservationResponse
from app.core.ports.ingest_port import IngestPort


class CreateReservationUseCase:
    """
    トラック予約作成 UseCase

    将来的な拡張予定:
      - 予約上限チェック
      - 重複予約のハンドリング
      - 予約履歴の記録
    """

    def __init__(self, ingest_repo: IngestPort):
        """
        Args:
            ingest_repo: データ永続化Port実装
        """
        self.ingest_repo = ingest_repo

    def execute(self, req: ReservationCreate) -> ReservationResponse:
        """
        トラック予約を作成/更新

        処理フロー:
          1. バリデーション（日付・台数チェック）
          2. DB保存（Port経由）
          3. レスポンス生成

        Args:
            req: 予約作成リクエスト

        Returns:
            予約作成結果

        Note:
            現状はスタブ実装。完全実装には以下が必要:
            - 予約ビジネスルールの明確化
            - 上限チェックロジック
            - 重複予約の扱い
        """
        # TODO: バリデーションロジック
        # TODO: ビジネスルール適用

        # DB保存（Port経由）
        result = self.ingest_repo.insert_reservation(
            date=req.date,
            trucks=req.trucks,
        )

        return ReservationResponse(
            date=req.date,
            trucks=req.trucks,
            created_at=datetime.utcnow(),
        )
