"""
Database infrastructure utilities for backend services.

DEPRECATED: This module has been moved to backend_shared.db
Please update your imports:
    from backend_shared.infra.db import ... → from backend_shared.db import ...

This compatibility layer will be removed in a future version.
"""

# Re-export from new location for backward compatibility
from backend_shared.db.url_builder import (
    build_postgres_dsn,
    build_database_url,
    build_database_url_with_driver,
)
from backend_shared.db.health import (
    DbHealth,
    ping_database,
)

__all__ = [
    "build_postgres_dsn",
    "build_database_url",
    "build_database_url_with_driver",
    "DbHealth",
    "ping_database",
]
