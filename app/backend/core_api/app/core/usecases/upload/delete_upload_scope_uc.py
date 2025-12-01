"""
Delete Upload Scope UseCase - アップロードスコープ削除ユースケース

指定されたアップロードファイルの特定日付・CSV種別のデータを論理削除します。
"""
import logging
from typing import Optional
from datetime import date

from app.core.ports.upload_status_port import IUploadStatusQuery
from backend_shared.application.logging import log_usecase_execution

logger = logging.getLogger(__name__)


class DeleteUploadScopeUseCase:
    """
    アップロードスコープ削除ユースケース
    
    責務:
      - パラメータのバリデーション
      - 論理削除の実行（Port経由）
      - 削除結果の記録
    """
    
    def __init__(self, query: IUploadStatusQuery):
        """
        Args:
            query: アップロードステータス管理の抽象インターフェース
        """
        self.query = query
    
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
        
        return affected_rows
