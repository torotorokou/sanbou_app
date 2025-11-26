"""
Adapters (Port の具体的な実装).

Hexagonal Architecture における「アダプター」を提供します。
各アダプターは core/ports で定義された抽象インターフェースを実装します。

👶 アダプターは外部ライブラリ（pandas, openpyxl, boto3 等）に依存しても構いません。
ビジネスロジック（core）はこれらを知らないため、技術選定の変更が容易です。
"""

from app.infra.adapters.csv import PandasCsvGateway
from app.infra.adapters.repository import FileSystemReportRepository

__all__ = [
    "PandasCsvGateway",
    "FileSystemReportRepository",
]
