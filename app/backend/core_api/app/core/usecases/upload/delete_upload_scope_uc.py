"""
Delete Upload Scope UseCase - アップロードスコープ削除ユースケース

指定されたアップロードファイルの特定日付・CSV種別のデータを論理削除します。

更新履歴:
  - 2025-12-12: CSV削除時のマテリアライズドビュー自動更新機能を追加
    将軍速報/最終版の受入CSV削除時にMV更新を実行
"""
import logging
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from app.core.ports.upload_status_port import IUploadCalendarQuery
from app.infra.adapters.materialized_view import MaterializedViewRefresher
from backend_shared.application.logging import log_usecase_execution, get_module_logger

logger = get_module_logger(__name__)


class DeleteUploadScopeUseCase:
    """
    アップロードスコープ削除ユースケース
    
    責務:
      - パラメータのバリデーション
      - 論理削除の実行（Port経由）
      - 削除結果の記録
      - CSV削除時のマテリアライズドビュー自動更新（受入CSVのみ）
    """
    
    def __init__(self, query: IUploadCalendarQuery, db: Session):
        """
        Args:
            query: アップロードカレンダー管理の抽象インターフェース
            db: SQLAlchemy Session (MV更新用)
        """
        self.query = query
        self.db = db
    
    @log_usecase_execution(usecase_name="DeleteUploadScope")
    def execute(
        self,
        upload_file_id: int,
        target_date: date,
        csv_kind: str,
        deleted_by: Optional[str] = None
    ) -> int:
        """
        指定されたアップロードスコープを論理削除
        
        Args:
            upload_file_id: 削除対象の log.upload_file.id
            target_date: 削除対象の日付
            csv_kind: CSV種別
            deleted_by: 削除実行者（オプション）
            
        Returns:
            影響を受けた行数
            
        Raises:
            ValueError: パラメータが不正な場合
            Exception: データベースエラー
            
        Note:
            トランザクション管理:
            - CSV削除とMV更新を同一トランザクション内で実行
            - 両方成功した場合のみコミット（FastAPIのget_db()経由）
            - どちらか失敗した場合はロールバック
        """
        # バリデーション
        if upload_file_id <= 0:
            raise ValueError(f"Invalid upload_file_id: {upload_file_id}")
        if not csv_kind:
            raise ValueError("csv_kind is required")
        
        logger.info(
            f"Deleting upload scope: upload_file_id={upload_file_id}, "
            f"date={target_date}, csv_kind={csv_kind}, deleted_by={deleted_by}"
        )
        
        try:
            # 論理削除の実行（Port経由）
            affected_rows = self.query.soft_delete_by_date_and_kind(
                upload_file_id=upload_file_id,
                target_date=target_date,
                csv_kind=csv_kind,
                deleted_by=deleted_by,
            )
            
            if affected_rows == 0:
                logger.warning(
                    f"No rows affected for upload_file_id={upload_file_id}, "
                    f"date={target_date}, csv_kind={csv_kind}"
                )
            else:
                logger.info(
                    f"Successfully deleted {affected_rows} rows for upload_file_id={upload_file_id}, "
                    f"date={target_date}, csv_kind={csv_kind}"
                )
            
            # CSV削除後のマテリアライズドビュー自動更新
            # 将軍速報/最終版の受入CSVのみ対応（receive関連のMVを更新）
            # auto_commit=Trueで各MV更新後にcommit()し、依存関係のあるMVが最新データを参照できるようにする
            self._refresh_materialized_views_if_needed(csv_kind)
            
            # 正常終了時はFastAPIのget_db()が自動的にcommit()
            # ただし、MV更新は既に各MVごとにcommit済み
            return affected_rows
            
        except Exception as e:
            # エラー時はFastAPIのget_db()が自動的にrollback()
            logger.error(
                f"Transaction failed during delete operation: "
                f"upload_file_id={upload_file_id}, date={target_date}, "
                f"csv_kind={csv_kind}, error={e}",
                exc_info=True
            )
            raise
    
    def _refresh_materialized_views_if_needed(self, csv_kind: str) -> None:
        """
        CSV削除後、必要に応じてマテリアライズドビューを更新
        
        Args:
            csv_kind: 削除されたCSV種別
                     例: 'shogun_flash_receive', 'shogun_final_receive'
        
        Note:
            受入CSV（receive）の場合のみMV更新を実行します。
            将軍速報版でも最終版でもMVは同じデータソースを参照するため、
            どちらが削除されてもMV更新が必要です。
            
            MaterializedViewRefresherが全てのロジックを統一的に処理します。
        """
        mv_refresher = MaterializedViewRefresher(self.db)
        mv_refresher.refresh_for_csv_kind(
            csv_kind=csv_kind,
            operation_name="mv_refresh_after_delete"
        )
