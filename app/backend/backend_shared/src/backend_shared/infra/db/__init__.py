"""
Database infrastructure utilities for backend services.

This module provides common database utilities:
- Database URL construction from environment variables
- Connection mode management (app / migrator separation)
- Health check functionality
- Connection helpers
"""

from backend_shared.infra.db.connection_mode import (
    DBConnectionMode,
    get_db_connection_params,
)
from backend_shared.infra.db.health import DbHealth, ping_database
from backend_shared.infra.db.url_builder import (
    build_database_url,
    build_database_url_with_driver,
    build_postgres_dsn,
)


__all__ = [
    "build_postgres_dsn",
    "build_database_url",
    "build_database_url_with_driver",
    "DbHealth",
    "ping_database",
    "DBConnectionMode",
    "get_db_connection_params",
]
