"""
Backward compatibility wrapper for inbound domain models.

DEPRECATED: This module is deprecated. Please use:
    from app.core.domain.inbound.entities import InboundDailyRow, CumScope

This wrapper will be removed in a future version.
"""
import warnings

warnings.warn(
    "Importing from app.core.domain.inbound is deprecated. "
    "Use app.core.domain.inbound.entities instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
from app.core.domain.inbound.entities import InboundDailyRow, CumScope

__all__ = ["InboundDailyRow", "CumScope"]
