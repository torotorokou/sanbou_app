"""
Core API Settings

環境変数とアプリケーション設定を管理するモジュール。
CSV→テーブルマッピングやDB接続情報などの設定を提供します。
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://myuser:mypassword@db:5432/sanbou_dev"
    )
    
    # CSV Upload Settings
    CSV_UPLOAD_MAX_SIZE: int = int(os.getenv("CSV_UPLOAD_MAX_SIZE", "10485760"))  # 10MB
    CSV_TEMP_DIR: str = os.getenv("CSV_TEMP_DIR", "/tmp/csv_uploads")
    
    # YAML設定ファイルパス（コンテナ内パス）
    CSV_MASTERS_YAML_PATH: str = os.getenv(
        "CSV_MASTERS_YAML_PATH",
        "/backend/config/csv_config/shogun_csv_masters.yaml"
    )
    
    # Shogun CSV Table Mapping (CSVタイプ → DBテーブル名)
    # フロントエンドから送られてくるキー名 → DBスキーマ.テーブル名
    CSV_TABLE_MAPPING: dict[str, str] = {
        "receive": "stg.receive_shogun_flash",    # 受入一覧
        "yard": "stg.yard_shogun_flash",          # ヤード一覧
        "shipment": "stg.shipment_shogun_flash",  # 出荷一覧
    }
    
    # Shogun CSV Schema Name
    SHOGUN_CSV_SCHEMA: str = os.getenv("SHOGUN_CSV_SCHEMA", "stg")
    
    # Shogun CSV Table Names (変更しやすいように個別に定義)
    RECEIVE_TABLE_NAME: str = os.getenv("RECEIVE_TABLE_NAME", "receive_shogun_flash")
    YARD_TABLE_NAME: str = os.getenv("YARD_TABLE_NAME", "yard_shogun_flash")
    SHIPMENT_TABLE_NAME: str = os.getenv("SHIPMENT_TABLE_NAME", "shipment_shogun_flash")
    
    # API Settings
    LEDGER_API_BASE: str = os.getenv("LEDGER_API_BASE", "http://ledger_api:8002")
    MANUAL_API_BASE: str = os.getenv("MANUAL_API_BASE", "http://manual_api:8003")
    AI_API_BASE: str = os.getenv("AI_API_BASE", "http://ai_api:8004")
    RAG_API_BASE: str = os.getenv("RAG_API_BASE", "http://rag_api:8005")
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend:5173",
    ]
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_table_name(self, csv_type: str) -> str:
        """
        CSVタイプから完全修飾テーブル名を取得
        
        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
            
        Returns:
            str: スキーマ.テーブル名 (例: 'raw.receive_shogun_flash')
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
            動的に生成されたORMモデルクラス
        """
        from app.infra.db.dynamic_models import get_shogun_model_class
        return get_shogun_model_class(csv_type)


@lru_cache()
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()
