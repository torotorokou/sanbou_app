"""
Database infrastructure utilities for backend services.

This module provides common database utilities:
- Database URL construction from environment variables
- Health check functionality
- Connection helpers
"""

from backend_shared.infra.db.url_builder import (
    build_database_url,
    build_database_url_with_driver,
)
from backend_shared.infra.db.health import (
    DbHealth,
    ping_database,
)

__all__ = [
    "build_database_url",
    "build_database_url_with_driver",
    "DbHealth",
    "ping_database",
]
