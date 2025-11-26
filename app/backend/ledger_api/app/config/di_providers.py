"""
Dependency Injection (DI) providers.

アプリケーションの依存関係を解決し、UseCase に注入します。

👶 初心者向け解説:
- DI（依存性注入）: オブジェクトが必要とする依存を外から渡す設計パターン
- このモジュールは「どの実装を使うか」を決定する中央ハブ
- 環境（dev/stg/prod）や設定に応じて、異なる実装を差し替え可能
"""

from functools import lru_cache

from app.core.usecases.reports import GenerateFactoryReportUseCase
from app.core.ports import CsvGateway, ReportRepository
from app.infra.adapters import PandasCsvGateway, FileSystemReportRepository


@lru_cache(maxsize=1)
def get_csv_gateway() -> CsvGateway:
    """
    CSV Gateway の実装を返す.

    現在は PandasCsvGateway を返すが、将来的に他の実装
    （例: PolarsCsvGateway）に差し替え可能。
    """
    return PandasCsvGateway()


@lru_cache(maxsize=1)
def get_report_repository() -> ReportRepository:
    """
    Report Repository の実装を返す.

    現在は FileSystemReportRepository を返すが、
    環境に応じて GCS や S3 の実装に差し替え可能。
    """
    return FileSystemReportRepository()


def get_factory_report_usecase() -> GenerateFactoryReportUseCase:
    """
    工場日報生成 UseCase を返す.

    依存する Port の実装を注入して UseCase を構築します。
    FastAPI の Depends() で利用されます。
    """
    return GenerateFactoryReportUseCase(
        csv_gateway=get_csv_gateway(),
        report_repository=get_report_repository(),
    )
