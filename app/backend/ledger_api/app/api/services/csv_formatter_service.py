"""
CSVフォーマッターサービス（後方互換性レイヤー）

このファイルは後方互換性のために残されています。
新しいコードでは app.api.services.csv.formatter_service を直接インポートしてください。

移行方法:
    旧: from app.api.services.csv_formatter_service import CsvFormatterService
    新: from app.api.services.csv.formatter_service import CsvFormatterService
    または: from app.api.services.csv import CsvFormatterService
"""

# 後方互換性のための再エクスポート
from app.api.services.csv.formatter_service import CsvFormatterService

__all__ = ["CsvFormatterService"]
