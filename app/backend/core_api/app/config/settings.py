"""
Core API Settings - アプリケーション設定管理

【概要】
環境変数とアプリケーション設定を一元管理するモジュール。
Pydantic Settings を使用した型安全な設定管理を提供します。

【主な機能】
1. データベース接続設定
2. CSV アップロード関連設定
3. Shogun CSV マッピング（CSV種別 → DBテーブル）
4. 外部APIエンドポイント設定
5. CORS設定

【設計方針】
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
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    
    環境変数から自動的に値を読み込み、型変換・検証を行います。
    環境変数が未設定の場合はデフォルト値を使用します。
    """
    
    # ========================================
    # データベース設定
    # ========================================
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://myuser:mypassword@db:5432/sanbou_dev"
    )
    """
    PostgreSQL接続URL
    
    形式: postgresql://user:password@host:port/database
    環境変数 DATABASE_URL で上書き可能
    """
    
    # ========================================
    # CSV アップロード設定
    # ========================================
    
    CSV_UPLOAD_MAX_SIZE: int = int(os.getenv("CSV_UPLOAD_MAX_SIZE", "10485760"))  # 10MB
    """CSVファイルの最大サイズ（バイト単位）デフォルト: 10MB"""
    
    CSV_TEMP_DIR: str = os.getenv("CSV_TEMP_DIR", "/tmp/csv_uploads")
    """CSV一時保存ディレクトリ（コンテナ内パス）"""
    
    CSV_MASTERS_YAML_PATH: str = os.getenv(
        "CSV_MASTERS_YAML_PATH",
        "/backend/config/csv_config/shogun_csv_masters.yaml"
    )
    """
    YAML設定ファイルパス（コンテナ内パス）
    
    Shogun Flash CSV のカラム定義・バリデーションルールを記載
    """
    
    # ========================================
    # Shogun CSV テーブルマッピング
    # ========================================
    
    CSV_TABLE_MAPPING: dict[str, str] = {
        "receive": "stg.shogun_flash_receive",    # 受入一覧
        "yard": "stg.shogun_flash_yard",          # ヤード一覧
        "shipment": "stg.shogun_flash_shipment",  # 出荷一覧
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
    # CORS設定（開発環境用）
    # ========================================
    
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",   # Vite開発サーバー
        "http://localhost:3000",   # 代替ポート
        "http://frontend:5173",    # Docker Compose内フロントエンド
    ]
    """
    CORS許可オリジンリスト
    
    開発環境でフロントエンドが別ドメインで動作する場合に使用
    本番環境ではnginxでCORS制御を行うため、通常は使用しない
    """
    
    # ========================================
    # Pydantic設定
    # ========================================
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
    
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
def get_settings() -> Settings:
    """
    設定のシングルトンインスタンスを取得
    
    Returns:
        Settings: アプリケーション設定インスタンス
        
    Description:
        @lru_cache() により、アプリケーション全体で1つのインスタンスのみを共有します。
        これにより環境変数の読み込みが1回のみで済み、パフォーマンスが向上します。
        
    Examples:
        >>> from app.config.settings import get_settings
        >>> settings = get_settings()
        >>> print(settings.DATABASE_URL)
    """
    return Settings()
