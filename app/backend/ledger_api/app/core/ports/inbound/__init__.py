"""
Port interfaces (抽象インターフェース).

Hexagonal Architecture における「ポート」を定義します。
UseCase 層はこれらの抽象に依存し、具体的な実装（Adapter）は知りません。

依存性逆転の原則（DIP）により、ビジネスロジックが外部技術から独立します。
"""

from app.core.ports.inbound.csv_gateway import CsvGateway
from app.core.ports.inbound.report_repository import ReportRepository, ArtifactUrls

__all__ = [
    "CsvGateway",
    "ReportRepository",
    "ArtifactUrls",
]
