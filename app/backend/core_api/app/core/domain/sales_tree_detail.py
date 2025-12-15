"""
Backward compatibility wrapper for sales_tree_detail domain models.

DEPRECATED: This module is deprecated. Please use:
    from app.core.domain.sales_tree.detail import ...

This wrapper will be removed in a future version.
"""
import warnings

warnings.warn(
    "Importing from app.core.domain.sales_tree_detail is deprecated. "
    "Use app.core.domain.sales_tree.detail instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
from app.core.domain.sales_tree.detail import (
    DetailMode,
    GroupBy,
    CategoryKind,
    DetailLinesRequest,
    DetailLine,
    DetailLinesResponse,
)

__all__ = [
    "DetailMode",
    "GroupBy",
    "CategoryKind",
    "DetailLinesRequest",
    "DetailLine",
    "DetailLinesResponse",
]
