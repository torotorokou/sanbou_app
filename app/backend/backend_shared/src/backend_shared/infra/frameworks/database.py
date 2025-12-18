"""
Database Session Management (Backward Compatibility)

⚠️ DEPRECATED: This module has been moved to backend_shared.db.session
Please update your imports:
    from backend_shared.infra.frameworks.database import DatabaseSessionManager
    → from backend_shared.db.session import DatabaseSessionManager

This compatibility layer will be removed in a future version.
"""
import warnings

# Re-export from new location for backward compatibility
from backend_shared.db.session import (
    DatabaseSessionManager,
    SyncDatabaseSessionManager,
)

# Issue deprecation warning on module import
warnings.warn(
    "backend_shared.infra.frameworks.database is deprecated. "
    "Use backend_shared.db.session instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "DatabaseSessionManager",
    "SyncDatabaseSessionManager",
]
