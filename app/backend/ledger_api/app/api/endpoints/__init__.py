"""Endpoints package initializer.

Staging 環境で `ModuleNotFoundError: app.api.endpoints.reports` が発生した場合、
ディレクトリ `endpoints/` に `__init__.py` が無いことで一部の解決パス / キャッシュが
不整合を起こした可能性があるため明示的にパッケージ化。

Points:
 - dev 環境は volume + reload で namespace package (PEP 420) が通るケースが多い
 - stg では build されたレイヤー内で import キャッシュ差異が起きやすいため通常パッケージ化
 - レポート系はサブパッケージ `reports` に集約
"""

# 明示 import (失敗時に早期にビルド段階で検知するため try を使わない)
from . import manage_report  # noqa: F401

# サブパッケージ経由で利用されるルーターを露出 (optional)
try:  # defensive (reports サブパッケージに問題があればログで把握)
    from .reports import reports_router  # type: ignore  # noqa: F401
except Exception as e:  # pragma: no cover
    # Lazy import fallback: runtime で参照される際に再度例外を投げる
    reports_router = None  # type: ignore
    import warnings

    warnings.warn(f"Failed to import reports subpackage: {e}")

__all__ = ["reports_router"]
