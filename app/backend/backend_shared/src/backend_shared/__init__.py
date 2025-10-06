"""
Backend Shared Package

共通ユーティリティ・ドメインモデル・ミドルウェアなどを提供します。

� パッケージ構造:
  - adapters/         # プレゼンテーション層・ミドルウェア・FastAPI統合
  - usecases/         # ビジネスロジック層
  - infrastructure/   # インフラストラクチャ層
  - domain/          # ドメインモデル
  - utils/           # 共通ユーティリティ

🔄 推奨されるインポートパス:
  - backend_shared.adapters.presentation
  - backend_shared.usecases.csv_validator
  - backend_shared.usecases.csv_formatter
  - backend_shared.usecases.report_checker
  - backend_shared.adapters.middleware
  - backend_shared.infrastructure.logging_utils
  - backend_shared.infrastructure.config
  - backend_shared.adapters.fastapi
"""

__version__ = "0.1.0"

__all__: list[str] = ["__version__"]
