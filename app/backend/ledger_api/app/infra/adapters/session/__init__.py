"""
Session management for interactive reports.

インタラクティブレポートのセッション状態管理を提供します。

モジュール:
- session_store: セッションストレージ（Redis/メモリ）
"""

from app.infra.adapters.session.session_store import SessionStore, session_store

__all__ = [
    "session_store",
    "SessionStore",
]
