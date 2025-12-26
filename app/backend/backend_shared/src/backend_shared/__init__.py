"""
Backend Shared Package

共通ユーティリティ・ドメインモデル・ミドルウェアなどを提供します。

🏗️ Clean Architecture 構成:
  - core/                  # コア層（ビジネスロジック）
    - domain/              # ドメインモデル（Entity, 値オブジェクト）
    - ports/               # 抽象インターフェース（Repository, Gateway）
    - usecases/            # アプリケーションロジック（UseCase）
  - infra/                 # インフラストラクチャ層
    - adapters/            # Ports の具体実装
      - fastapi/           # FastAPI 統合
      - middleware/        # ミドルウェア
      - presentation/      # プレゼンテーション層
    - frameworks/          # フレームワーク固有処理
  - config/                # 設定管理・DI
  - utils/                 # 共通ユーティリティ

🔄 推奨されるインポートパス:
  # Domain & Use Cases
  - backend_shared.core.domain
  - backend_shared.core.usecases.csv_validator
  - backend_shared.core.usecases.csv_formatter

  # Infrastructure
  - backend_shared.infra.adapters.presentation
  - backend_shared.infra.adapters.middleware
  - backend_shared.infra.adapters.fastapi
  - backend_shared.infra.frameworks.database

  # Configuration & DI
  - backend_shared.config.config_loader
  - backend_shared.config.di_providers

  # Database (DB関連全機能)
  - backend_shared.db (names, url_builder, health, shogun)

📐 依存関係のルール:
  - core は他のどの層にも依存しない
  - infra は core に依存する（依存関係逆転）
  - config で依存関係を組み立てる
"""

__version__ = "0.2.1"  # 将軍データセット取得クラス追加

__all__: list[str] = ["__version__"]
