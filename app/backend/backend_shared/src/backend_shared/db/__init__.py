"""Database module - DB object name constants and utilities."""

from backend_shared.db.names import (  # Schemas; Helper functions; Object collections
    ALL_MART_MVS,
    AUTO_REFRESH_MVS,
    FIVE_YEAR_AVG_MVS,
    SCHEMA_KPI,
    SCHEMA_LOG,
    SCHEMA_MART,
    SCHEMA_RAW,
    SCHEMA_REF,
    SCHEMA_STG,
    SHOGUN_ACTIVE_VIEWS,
    SHOGUN_FINAL_TABLES,
    SHOGUN_FLASH_TABLES,
    fq,
    schema_qualified,
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
]
