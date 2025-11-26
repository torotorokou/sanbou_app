"""
File System Report Repository (ファイルシステムへのレポート保存実装).

👶 このクラスは ReportRepository Port の具体的な実装です。
既存の artifacts/artifact_service を活用します。
"""

from datetime import date
from io import BytesIO
from typing import Optional

from app.core.ports import ReportRepository
from app.core.ports.report_repository import ArtifactUrls
from app.api.services.report.artifacts import get_report_artifact_storage


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
        # ArtifactLocation を確保
        location = self._storage.allocate(
            report_key=report_key,
            report_date=report_date.isoformat(),
        )

        # Excel と PDF を保存
        excel_content = excel_bytes.getvalue() if hasattr(excel_bytes, 'getvalue') else excel_bytes.read()
        pdf_content = pdf_bytes.getvalue() if hasattr(pdf_bytes, 'getvalue') else pdf_bytes.read()

        self._storage.save_excel(location, excel_content)
        self._storage.save_pdf(location, pdf_content)

        # 署名付き URL を生成
        payload = self._storage.build_payload(location, excel_exists=True, pdf_exists=True)

        return ArtifactUrls(
            excel_url=payload["excel_download_url"],
            pdf_url=payload["pdf_preview_url"],
            zip_url=None,  # 既存実装には zip がないため None
        )

    def get_artifact_urls(
        self,
        report_key: str,
        report_date: date,
        timestamp_token: str,
    ) -> Optional[ArtifactUrls]:
        """
        既存のアーティファクトの URL を取得.

        TODO: 現時点では未実装（将来の拡張用）。
        """
        # 既存の artifact_service には検索機能がないため、
        # 必要に応じて後で実装します。
        return None
