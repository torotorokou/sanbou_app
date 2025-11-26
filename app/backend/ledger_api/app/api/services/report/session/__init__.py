"""
Backward compatibility for session management.

新しい場所: app.infra.adapters.session
"""

from app.infra.adapters.session import (
    session_store,
    SessionStore,
)

__all__ = [
    "session_store",
    "SessionStore",
]
