"""
Database module - DB object name constants and utilities.

This module consolidates all database-related functionality:
- Object name constants (names.py)
- Database URL construction (url_builder.py)
- Health check utilities (health.py)
- Shogun dataset access (shogun/)
"""

# DB Object Names
from backend_shared.db.names import (
    # Schemas
    SCHEMA_REF,
    SCHEMA_STG,
    SCHEMA_MART,
    SCHEMA_KPI,
    SCHEMA_RAW,
    SCHEMA_LOG,
    # Helper functions
    fq,
    schema_qualified,
    # Object collections
    ALL_MART_MVS,
    AUTO_REFRESH_MVS,
    FIVE_YEAR_AVG_MVS,
    SHOGUN_FINAL_TABLES,
    SHOGUN_FLASH_TABLES,
    SHOGUN_ACTIVE_VIEWS,
)

# DB Connection Utilities
from backend_shared.db.url_builder import (
    build_postgres_dsn,
    build_database_url,
    build_database_url_with_driver,
)
from backend_shared.db.health import (
    DbHealth,
    ping_database,
)

# Shogun Dataset Access
from backend_shared.db.shogun import (
    ShogunDatasetKey,
    ShogunDatasetFetcher,
    ShogunMasterNameMapper,
)

__all__ = [
    # Schemas
    "SCHEMA_REF",
    "SCHEMA_STG",
    "SCHEMA_MART",
    "SCHEMA_KPI",
    "SCHEMA_RAW",
    "SCHEMA_LOG",
    # Helper functions
    "fq",
    "schema_qualified",
    # Object collections
    "ALL_MART_MVS",
    "AUTO_REFRESH_MVS",
    "FIVE_YEAR_AVG_MVS",
    "SHOGUN_FINAL_TABLES",
    "SHOGUN_FLASH_TABLES",
    "SHOGUN_ACTIVE_VIEWS",
    # Connection utilities
    "build_postgres_dsn",
    "build_database_url",
    "build_database_url_with_driver",
    "DbHealth",
    "ping_database",
    # Shogun dataset access
    "ShogunDatasetKey",
    "ShogunDatasetFetcher",
    "ShogunMasterNameMapper",
]
