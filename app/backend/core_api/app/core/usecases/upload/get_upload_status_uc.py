"""
Get Upload Status UseCase - アップロードステータス取得ユースケース

指定されたアップロードファイルの処理状態を取得します。
"""

from typing import Any

from app.core.ports.upload_status_port import IUploadStatusQuery
from backend_shared.application.logging import (
    create_log_context,
    get_module_logger,
    log_usecase_execution,
)

logger = get_module_logger(__name__)


class GetUploadStatusUseCase:
    """
    アップロードステータス取得ユースケース

    責務:
      - upload_file_id のバリデーション
      - ステータス情報の取得（Port経由）
      - 見つからない場合の通知
    """

    def __init__(self, query: IUploadStatusQuery):
        """
        Args:
            query: アップロードステータス取得の抽象インターフェース
        """
        self.query = query

    @log_usecase_execution(usecase_name="GetUploadStatus")
    def execute(self, upload_file_id: int) -> dict[str, Any] | None:
        """
        アップロードファイルのステータスを取得

        Args:
            upload_file_id: log.upload_file.id

        Returns:
            アップロード情報の辞書、または None（見つからない場合）

        Raises:
            ValueError: upload_file_id が不正な場合
            Exception: データベースエラー
        """
        # バリデーション
        if upload_file_id <= 0:
            raise ValueError(f"Invalid upload_file_id: {upload_file_id}")

        logger.info(
            "アップロードステータス取得開始",
            extra=create_log_context(
                operation="get_upload_status", upload_file_id=upload_file_id
            ),
        )

        # データ取得（Port経由）
        status = self.query.get_upload_status(upload_file_id)

        if status is None:
            logger.warning(
                "アップロードファイル未検出",
                extra=create_log_context(
                    operation="get_upload_status", upload_file_id=upload_file_id
                ),
            )
        else:
            logger.info(
                "アップロードステータス取得成功",
                extra=create_log_context(
                    operation="get_upload_status",
                    upload_file_id=upload_file_id,
                    status=status.get("processing_status"),
                ),
            )

        return status
