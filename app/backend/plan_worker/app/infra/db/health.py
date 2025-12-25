"""Database health check utility.

Note:
    このモジュールは backend_shared.infra.db.health からインポートする形に移行しました。
    後方互換性のため、既存のインポートは引き続き動作します。
"""

from __future__ import annotations

from backend_shared.infra.db.health import DbHealth, ping_database


def ping_db(timeout_sec: int = 2) -> DbHealth:
    """
    Ping database and return health status.

    Note:
        この関数は後方互換性のためのラッパーです。
        新しいコードでは backend_shared.infra.db.health.ping_database() を直接使用してください。

    Args:
        timeout_sec: Connection timeout in seconds (default: 2)

    Returns:
        DbHealth object with connection result
    """
    return ping_database(timeout_sec=timeout_sec)
