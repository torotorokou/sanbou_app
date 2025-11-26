"""
Report generation UseCases.

各種帳票生成の UseCase を提供します。
"""

from app.core.usecases.reports.generate_factory_report import (
    GenerateFactoryReportUseCase,
)

__all__ = [
    "GenerateFactoryReportUseCase",
]
