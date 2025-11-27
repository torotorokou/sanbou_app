"""
Report Repository Port (レポート保存の抽象インターフェース).

👶 初心者向け解説:
- Repository: ドメインオブジェクトの永続化を抽象化するパターン
- このポートは「レポートをどこかに保存し、アクセス可能な URL を返す」責務を定義
- 実装（Adapter）は、ファイルシステム、GCS、S3 など様々な選択肢がある
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import Dict, Optional


@dataclass(frozen=True)
class ArtifactUrls:
    """生成されたレポートアーティファクトの URL を格納する値オブジェクト."""

    excel_url: str
    pdf_url: str
    zip_url: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """辞書形式に変換（JSON レスポンス用）."""
        result = {
            "excel_url": self.excel_url,
            "pdf_url": self.pdf_url,
        }
        if self.zip_url:
            result["zip_url"] = self.zip_url
        return result


class ReportRepository(ABC):
    """レポートアーティファクトの保存と URL 生成の抽象インターフェース."""

    @abstractmethod
    def save_report(
        self,
        report_key: str,
        report_date: date,
        excel_bytes: BytesIO,
        pdf_bytes: BytesIO,
    ) -> ArtifactUrls:
        """
        レポートを保存し、署名付き URL を返す.

        Args:
            report_key: レポート種別（例: "factory_report"）
            report_date: レポート対象日
            excel_bytes: Excel ファイルのバイトストリーム
            pdf_bytes: PDF ファイルのバイトストリーム

        Returns:
            ArtifactUrls: Excel/PDF の署名付き URL

        Notes:
            👶 この抽象メソッドは「どこに保存するか」を知りません。
            実装（Adapter）が、ファイルシステムや GCS に保存します。
        """
        pass

    @abstractmethod
    def get_artifact_urls(
        self,
        report_key: str,
        report_date: date,
        timestamp_token: str,
    ) -> Optional[ArtifactUrls]:
        """
        既存のアーティファクトの URL を取得.

        Args:
            report_key: レポート種別
            report_date: レポート対象日
            timestamp_token: タイムスタンプ付きトークン（例: "20251126_123456-abc12345"）

        Returns:
            ArtifactUrls または None（存在しない場合）
        """
        pass
