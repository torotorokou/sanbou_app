"""
Backend Shared Package

共通ユーティリティ・ドメインモデル・ミドルウェアなどを提供します。

🔄 移行ガイド:
旧パスと新パスの対応関係:
  - backend_shared.api_response → backend_shared.adapters.presentation
  - backend_shared.csv_validator → backend_shared.usecases.csv_validator
  - backend_shared.csv_formatter → backend_shared.usecases.csv_formatter
  - backend_shared.report_checker → backend_shared.usecases.report_checker
  - backend_shared.middleware → backend_shared.adapters.middleware
  - backend_shared.logging_utils → backend_shared.infrastructure.logging_utils
  - backend_shared.config → backend_shared.infrastructure.config
  - backend_shared.api → backend_shared.adapters.fastapi

後方互換性のため、旧パスから新パスへのエイリアスを提供していますが、
新規コードでは新パスを使用することを推奨します。
"""

import sys
from typing import Any

__version__ = "0.1.0"

# 後方互換性のための動的エイリアス設定
_LEGACY_MODULE_MAP = {
    "backend_shared.api_response": "backend_shared.adapters.presentation",
    "backend_shared.csv_validator": "backend_shared.usecases.csv_validator",
    "backend_shared.csv_formatter": "backend_shared.usecases.csv_formatter",
    "backend_shared.report_checker": "backend_shared.usecases.report_checker",
    "backend_shared.middleware": "backend_shared.adapters.middleware",
    "backend_shared.logging_utils": "backend_shared.infrastructure.logging_utils",
    "backend_shared.config": "backend_shared.infrastructure.config",
    "backend_shared.api": "backend_shared.adapters.fastapi",
}


class _LegacyModuleProxy:
    """旧パスから新パスへのプロキシモジュール"""

    def __init__(self, target_module: str):
        self._target_module = target_module

    def __getattr__(self, name: str) -> Any:
        import importlib
        module = importlib.import_module(self._target_module)
        return getattr(module, name)


def _setup_legacy_imports():
    """旧パスからのインポートを動的にサポート"""
    for legacy_path, new_path in _LEGACY_MODULE_MAP.items():
        if legacy_path not in sys.modules:
            sys.modules[legacy_path] = _LegacyModuleProxy(new_path)


_setup_legacy_imports()

__all__: list[str] = ["__version__"]
