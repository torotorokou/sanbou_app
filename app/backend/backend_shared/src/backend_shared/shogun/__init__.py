"""
Shogun dataset access module.

DEPRECATED: This module has been moved to backend_shared.db.shogun
Please update your imports:
    from backend_shared.shogun import ... → from backend_shared.db.shogun import ...

This compatibility layer will be removed in a future version.
"""

# Re-export from new location for backward compatibility
from backend_shared.db.shogun import (
    ShogunDatasetKey,
    ShogunDatasetFetcher,
    ShogunMasterNameMapper,
)

__all__ = [
    "ShogunDatasetKey",
    "ShogunDatasetFetcher",
    "ShogunMasterNameMapper",
]
