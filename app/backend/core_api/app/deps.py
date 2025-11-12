"""
Dependency injection and utilities for FastAPI.

This module re-exports get_db from app.infra.db for backwards compatibility
and to serve as a centralized place for all FastAPI dependencies.
"""
from app.infra.db import get_db  # noqa: F401

__all__ = ["get_db"]
