"""
Backward compatibility layer for app.api.config (DEPRECATED).

Use app.config instead.
"""
# Re-export from new location
from app.config.loader import *  # noqa
from app.config.settings import *  # noqa

__all__ = []
