"""
Report generation UseCases.

各種帳票生成の UseCase を提供します。
"""

from app.application.usecases.reports.generate_factory_report import (
    GenerateFactoryReportUseCase,
)

__all__ = [
    "GenerateFactoryReportUseCase",
]
