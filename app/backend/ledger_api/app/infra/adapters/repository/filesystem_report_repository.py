"""
File System Report Repository (ファイルシステムへのレポート保存実装).

👶 このクラスは ReportRepository Port の具体的な実装です。
既存の artifacts/artifact_service を活用します。
"""

import time
from datetime import date
from io import BytesIO
from typing import Optional

from app.core.ports.inbound import ReportRepository
from app.core.ports.inbound.report_repository import ArtifactUrls
from app.infra.adapters.artifact_storage import get_report_artifact_storage
from backend_shared.application.logging import create_log_context, get_module_logger

logger = get_module_logger(__name__)


class FileSystemReportRepository(ReportRepository):
    """ファイルシステムを使った Report Repository の実装."""

    def __init__(self):
        """初期化（既存の artifact storage を利用）."""
        self._storage = get_report_artifact_storage()

    def save_report(
        self,
        report_key: str,
        report_date: date,
        excel_bytes: BytesIO,
        pdf_bytes: BytesIO,
    ) -> ArtifactUrls:
        """
        レポートをファイルシステムに保存し、署名付き URL を返す.

        既存の ReportArtifactStorage を利用します。
        """
        start_time = time.time()

        logger.info(
            "レポート保存開始",
            extra={
                "operation": "save_report",
                "report_key": report_key,
                "report_date": report_date.isoformat(),
            },
        )

        location = None
        excel_saved = False
        pdf_saved = False

        try:
            # ArtifactLocation を確保
            location = self._storage.allocate(
                report_key=report_key,
                report_date=report_date.isoformat(),
            )

            logger.debug(
                "Artifactロケーション確保完了",
                extra={
                    "operation": "save_report",
                    "report_key": report_key,
                    "location": str(location),
                },
            )

            # Excel と PDF のバイトデータを取得
            excel_content = (
                excel_bytes.getvalue()
                if hasattr(excel_bytes, "getvalue")
                else excel_bytes.read()
            )
            pdf_content = (
                pdf_bytes.getvalue()
                if hasattr(pdf_bytes, "getvalue")
                else pdf_bytes.read()
            )

            excel_size = len(excel_content)
            pdf_size = len(pdf_content)

            # Excel を保存
            self._storage.save_excel(location, excel_content)
            excel_saved = True
            logger.debug(
                "Excel保存完了",
                extra={
                    "operation": "save_report",
                    "report_key": report_key,
                    "size_bytes": excel_size,
                },
            )

            # PDF を保存
            self._storage.save_pdf(location, pdf_content)
            pdf_saved = True
            logger.debug(
                "PDF保存完了",
                extra={
                    "operation": "save_report",
                    "report_key": report_key,
                    "size_bytes": pdf_size,
                },
            )

            # 署名付き URL を生成
            payload = self._storage.build_payload(
                location, excel_exists=True, pdf_exists=True
            )

            urls = ArtifactUrls(
                excel_url=payload["excel_download_url"],
                pdf_url=payload["pdf_preview_url"],
                zip_url=None,  # 既存実装には zip がないため None
            )

            elapsed = time.time() - start_time
            logger.info(
                "レポート保存完了",
                extra={
                    "operation": "save_report",
                    "report_key": report_key,
                    "report_date": report_date.isoformat(),
                    "excel_size_bytes": excel_size,
                    "pdf_size_bytes": pdf_size,
                    "elapsed_seconds": round(elapsed, 3),
                },
            )

            return urls

        except Exception as e:
            elapsed = time.time() - start_time

            # エラー情報を詳細にログ出力
            logger.exception(
                "レポート保存中にエラー",
                extra={
                    "operation": "save_report",
                    "report_key": report_key,
                    "report_date": report_date.isoformat(),
                    "excel_saved": excel_saved,
                    "pdf_saved": pdf_saved,
                    "elapsed_seconds": round(elapsed, 3),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
            )

            # NOTE: 部分保存済みファイルのクリーンアップは現状不要
            # 理由: 既存の storage が自動的にタイムスタンプ付きディレクトリを作成するため、
            #       失敗時はそのディレクトリごと削除することが理想だが、現在は問題が発生していない。

            # エラーを再送出（UseCase層でキャッチされる）
            raise

    def get_artifact_urls(
        self,
        report_key: str,
        report_date: date,
        timestamp_token: str,
    ) -> Optional[ArtifactUrls]:
        """
        既存のアーティファクトの URL を取得.

        FUTURE: 現時点では未実装（将来の拡張用）。
        理由: 既存の artifact_service には検索機能がないため、
              必要に応じて後で実装します。
        """
        return None
