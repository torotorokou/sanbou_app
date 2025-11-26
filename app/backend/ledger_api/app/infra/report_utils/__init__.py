"""Report generation infrastructure utilities."""

from .excel_writer import write_values_to_template
from .template_config import get_template_config

__all__ = [
    "write_values_to_template",
    "get_template_config",
]
