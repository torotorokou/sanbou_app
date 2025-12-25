"""
Config パッケージ - 設定管理モジュール

【概要】
環境変数の読み込み、設定の管理を行うモジュール群を提供します。

【主なモジュール】
- env_utils: 環境変数ユーティリティ（共通化された環境変数読み込み）
- config_loader: 設定ファイルの読み込み
- paths: パス管理
- di_providers: 依存性注入プロバイダ

【使用例】
```python
from backend_shared.config.env_utils import (
    is_debug_mode,
    is_iap_enabled,
    get_stage,
)

if is_debug_mode():
    print("Debug mode enabled")
```
"""

# 環境変数ユーティリティをエクスポート
from .env_utils import (
    get_api_base_url,
    get_bool_env,
    get_database_url,
    get_iap_audience,
    get_int_env,
    get_log_level,
    get_stage,
    get_str_env,
    is_debug_mode,
    is_development,
    is_iap_enabled,
    is_production,
)

__all__ = [
    # 汎用環境変数読み込み
    "get_bool_env",
    "get_int_env",
    "get_str_env",
    # 共通環境変数
    "is_debug_mode",
    "is_iap_enabled",
    "get_iap_audience",
    "get_stage",
    "is_production",
    "is_development",
    "get_api_base_url",
    "get_database_url",
    "get_log_level",
]
