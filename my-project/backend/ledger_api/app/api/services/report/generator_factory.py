# backend/app/api/services/generator_factory.py

from typing import Dict, Any
from .concrete_generators import (
    FactoryReportGenerator,
    BalanceSheetGenerator,
    AverageSheetGenerator,
    BlockUnitPriceGenerator,
    ManagementSheetGenerator,
)
from .base_report_generator import BaseReportGenerator


def get_report_generator(report_key: str, files: Dict[str, Any]) -> BaseReportGenerator:
    """
    帳簿種別に応じて適切なGeneratorを返す
    """
    generators = {
        "factory_report": FactoryReportGenerator,
        "balance_sheet": BalanceSheetGenerator,
        "average_sheet": AverageSheetGenerator,
        "block_unit_price": BlockUnitPriceGenerator,
        "management_sheet": ManagementSheetGenerator,
    }
    if report_key not in generators:
        available_keys = list(generators.keys())
        raise ValueError(
            f"Unsupported report type: {report_key}. Available types: {available_keys}"
        )
    generator_class = generators[report_key]
    return generator_class(report_key, files)
