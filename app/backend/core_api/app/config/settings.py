"""
Core API Settings - アプリケーション設定管理

【概要】
環境変数とアプリケーション設定を一元管理するモジュール。
backend_shared の BaseAppSettings を継承し、Core API固有の設定を追加します。

【主な機能】
1. データベース接続設定
2. CSV アップロード関連設定
3. Shogun CSV マッピング（CSV種別 → DBテーブル）
4. 外部APIエンドポイント設定

【設計方針】
- BaseAppSettings により共通設定を継承
- 12 Factor App に基づく環境変数ベース設定
- デフォルト値の提供により開発環境でも動作
- 型安全性（Pydantic による検証）
- シングルトンパターン（@lru_cache による1インスタンスのみ保証）

【使用例】
```python
from app.config.settings import get_settings

settings = get_settings()
db_url = settings.DATABASE_URL
table_name = settings.get_table_name('receive')
```
"""

import os
from functools import lru_cache

from backend_shared.config.base_settings import BaseAppSettings
from backend_shared.db.names import (
    SCHEMA_STG,
    T_SHOGUN_FLASH_RECEIVE,
    T_SHOGUN_FLASH_SHIPMENT,
    T_SHOGUN_FLASH_YARD,
    schema_qualified,
)


class CoreApiSettings(BaseAppSettings):
    """
    Core API 設定クラス

    BaseAppSettings を継承し、Core API 固有の設定を追加します。
    環境変数から自動的に値を読み込み、型変換・検証を行います。
    """

    # ========================================
    # API基本情報
    # ========================================

    API_TITLE: str = "CORE_API"
    API_VERSION: str = "1.0.0"

    # ========================================
    # データベース設定
    # ========================================

    @staticmethod
    def _build_database_url() -> str:
        """環境変数からDATABASE_URLを構築"""
        from backend_shared.infra.db.url_builder import build_database_url

        return build_database_url(driver=None, raise_on_missing=True)

    DATABASE_URL: str = _build_database_url.__func__()
    """
    PostgreSQL接続URL

    形式: postgresql://user:password@host:port/database
    環境変数 DATABASE_URL で上書き可能
    環境変数が未設定の場合は POSTGRES_* 環境変数から動的に構築
    """

    # ========================================
    # CSV アップロード設定
    # ========================================

    CSV_UPLOAD_MAX_SIZE: int = int(os.getenv("CSV_UPLOAD_MAX_SIZE", "10485760"))  # 10MB
    """CSVファイルの最大サイズ（バイト単位）デフォルト: 10MB"""

    CSV_TEMP_DIR: str = os.getenv("CSV_TEMP_DIR", "/tmp/csv_uploads")
    """CSV一時保存ディレクトリ（コンテナ内パス）"""

    CSV_MASTERS_YAML_PATH: str = os.getenv(
        "CSV_MASTERS_YAML_PATH", "/backend/config/csv_config/shogun_csv_masters.yaml"
    )
    """
    YAML設定ファイルパス（コンテナ内パス）

    Shogun Flash CSV のカラム定義・バリデーションルールを記載
    """

    # ========================================
    # Shogun CSV テーブルマッピング
    # ========================================

    CSV_TABLE_MAPPING: dict[str, str] = {
        "receive": schema_qualified(SCHEMA_STG, T_SHOGUN_FLASH_RECEIVE),  # 受入一覧
        "yard": schema_qualified(SCHEMA_STG, T_SHOGUN_FLASH_YARD),  # ヤード一覧
        "shipment": schema_qualified(SCHEMA_STG, T_SHOGUN_FLASH_SHIPMENT),  # 出荷一覧
    }
    """
    CSVタイプ → DBテーブル名のマッピング

    フロントエンドから送られてくるCSV種別キー（receive, yard, shipment）を
    実際のデータベーステーブル名（スキーマ.テーブル）に変換します。
    """

    SHOGUN_CSV_SCHEMA: str = os.getenv("SHOGUN_CSV_SCHEMA", "stg")
    """Shogun CSV データを格納するスキーマ名（デフォルト: stg）"""

    RECEIVE_TABLE_NAME: str = os.getenv("RECEIVE_TABLE_NAME", "shogun_flash_receive")
    """受入一覧テーブル名（スキーマなし）"""

    YARD_TABLE_NAME: str = os.getenv("YARD_TABLE_NAME", "shogun_flash_yard")
    """ヤード一覧テーブル名（スキーマなし）"""

    SHIPMENT_TABLE_NAME: str = os.getenv("SHIPMENT_TABLE_NAME", "shogun_flash_shipment")
    """出荷一覧テーブル名（スキーマなし）"""

    # ========================================
    # 外部APIエンドポイント設定
    # ========================================

    LEDGER_API_BASE: str = os.getenv("LEDGER_API_BASE", "http://ledger_api:8002")
    """
    Ledger API ベースURL

    帳簿・会計データを管理するマイクロサービス
    - 売上データ、入金データ、請求データなど
    """

    MANUAL_API_BASE: str = os.getenv("MANUAL_API_BASE", "http://manual_api:8003")
    """
    Manual API ベースURL

    マニュアル・ドキュメント検索サービス
    - 業務マニュアル、FAQ、手順書など
    """

    AI_API_BASE: str = os.getenv("AI_API_BASE", "http://ai_api:8004")
    """
    AI API ベースURL

    機械学習・AI機能を提供するサービス
    - 予測、分類、異常検知など
    """

    RAG_API_BASE: str = os.getenv("RAG_API_BASE", "http://rag_api:8005")
    """
    RAG (Retrieval-Augmented Generation) API ベースURL

    文書検索とLLM を組み合わせた回答生成サービス
    - チャットボット、質問応答など
    """

    # ========================================
    # 認証設定（IAP: Identity-Aware Proxy）
    # ========================================

    IAP_ENABLED: bool = os.getenv("IAP_ENABLED", "false").lower() == "true"
    """
    Google Cloud IAP認証の有効/無効

    本番環境では必ずTrueに設定してください。
    環境変数 IAP_ENABLED=true で有効化
    """

    IAP_AUDIENCE: str | None = os.getenv("IAP_AUDIENCE")
    """
    Google Cloud IAP オーディエンス

    GCP Console > Security > Identity-Aware Proxy から取得
    形式: /projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID
    本番環境では必須
    """

    ALLOWED_EMAIL_DOMAIN: str = os.getenv("ALLOWED_EMAIL_DOMAIN", "example.com")
    """
    許可するメールドメイン

    IAP認証で許可するGoogleアカウントのドメイン
    例: "yourcompany.com"
    """

    # ========================================
    # Pydantic設定
    # ========================================

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    # ========================================
    # ヘルパーメソッド
    # ========================================

    def get_table_name(self, csv_type: str) -> str:
        """
        CSVタイプから完全修飾テーブル名を取得

        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')

        Returns:
            str: スキーマ.テーブル名 (例: 'stg.shogun_flash_receive')

        Examples:
            >>> settings = get_settings()
            >>> settings.get_table_name('receive')
            'stg.shogun_flash_receive'
            >>> settings.get_table_name('yard')
            'stg.shogun_flash_yard'
        """
        table_mapping = {
            "receive": f"{self.SHOGUN_CSV_SCHEMA}.{self.RECEIVE_TABLE_NAME}",
            "yard": f"{self.SHOGUN_CSV_SCHEMA}.{self.YARD_TABLE_NAME}",
            "shipment": f"{self.SHOGUN_CSV_SCHEMA}.{self.SHIPMENT_TABLE_NAME}",
        }
        return table_mapping.get(csv_type, "")

    def get_orm_model_class(self, csv_type: str):
        """
        CSVタイプからORMモデルクラスを取得（動的生成版）

        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')

        Returns:
            動的に生成されたSQLAlchemy ORMモデルクラス

        Description:
            YAMLファイルで定義されたカラム情報から、
            実行時にORMモデルクラスを動的生成します。
            これによりYAML変更時にPythonコード修正が不要になります。

        Examples:
            >>> settings = get_settings()
            >>> ReceiveModel = settings.get_orm_model_class('receive')
            >>> # ReceiveModel を使ってCRUD操作
        """
        from app.infra.db.dynamic_models import get_shogun_model_class

        return get_shogun_model_class(csv_type)


@lru_cache()
def get_settings() -> CoreApiSettings:
    """
    設定のシングルトンインスタンスを取得

    Returns:
        CoreApiSettings: Core API設定インスタンス

    Description:
        @lru_cache() により、アプリケーション全体で1つのインスタンスのみを共有します。
        これにより環境変数の読み込みが1回のみで済み、パフォーマンスが向上します。

    Examples:
        >>> from app.config.settings import get_settings
        >>> settings = get_settings()
        >>> print(settings.DATABASE_URL)
    """
    return CoreApiSettings()


# シングルトンインスタンス
settings = get_settings()

__all__ = ["settings", "CoreApiSettings", "get_settings"]
