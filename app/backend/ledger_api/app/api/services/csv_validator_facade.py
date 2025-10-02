"""
CSVバリデーターファサードサービス（後方互換性レイヤー）

このファイルは後方互換性のために残されています。
新しいコードでは app.api.services.csv.validator_service を直接インポートしてください。

移行方法:
    旧: from app.api.services.csv_validator_facade import CsvValidatorService
    新: from app.api.services.csv.validator_service import CsvValidatorService
    または: from app.api.services.csv import CsvValidatorService
"""

# 後方互換性のための再エクスポート
from app.api.services.csv.validator_service import CsvValidatorService

__all__ = ["CsvValidatorService"]
