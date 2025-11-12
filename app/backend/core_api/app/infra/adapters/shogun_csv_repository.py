# implements Port: IShogunCsvWriter (app/ports/csv_writer.py)
"""
Adapter: ShogunCsvRepository

将軍CSVデータをDBに保存するアダプター。
IShogunCsvWriter ポートを実装し、具体的なDB操作（SQLAlchemy ORM）を担当。

設計方針:
  - Port (IShogunCsvWriter) を実装
  - schema/table_map による切替を吸収
  - YAMLベースのカラムマッピングを活用
  - ORM操作の具体を隠蔽
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.repositories.core.dynamic_models import get_shogun_model_class, create_shogun_model_class
from app.config.settings import get_settings
from app.config.table_definition import get_table_definition_generator

logger = logging.getLogger(__name__)


class ShogunCsvRepository:
    """将軍CSV保存リポジトリ（IShogunCsvWriter実装）"""
    
    def __init__(
        self,
        db: Session,
        table_map: dict[str, str] | None = None,
        schema: str | None = None,
    ):
        """
        Args:
            db: SQLAlchemy Session
            table_map: テーブル名マッピング（オプション）
                例: {"receive": "receive_flash", "yard": "yard_flash", "shipment": "shipment_flash"}
            schema: スキーマ名（オプション、デフォルトは search_path に従う）
        """
        self.db = db
        self.settings = get_settings()
        self.table_gen = get_table_definition_generator()
        self._table_map = table_map or {}  # テーブル名上書き用
        self._schema = schema  # 将来的にORM側でも利用可能
    
    def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
        """
        CSV種別に応じて適切なテーブルに保存
        
        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
            df: 保存するDataFrame（英語カラム名）
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {csv_type}, skipping save")
            return 0
        
        # テーブル名の上書きチェック
        override_table = self._table_map.get(csv_type)
        if override_table:
            # table_map が指定された場合のみ _save_to_table を呼ぶ
            return self._save_to_table(csv_type, df, override_table)
        
        # デフォルトルート: 従来の保存処理
        model_class = get_shogun_model_class(csv_type)
        
        # YAMLからカラム定義を取得
        columns_def = self.table_gen.get_columns_definition(csv_type)
        valid_columns = {col['en_name'] for col in columns_def}
        
        # DataFrameのカラムを検証
        df_columns = set(df.columns)
        missing_in_yaml = df_columns - valid_columns
        if missing_in_yaml:
            logger.warning(f"Columns in DataFrame but not in YAML for {csv_type}: {missing_in_yaml}")
        
        # DataFrameを辞書のリストに変換
        records = df.to_dict('records')
        
        # ORMオブジェクトのリストを作成
        orm_objects = []
        for record in records:
            # YAMLで定義されたカラムのみ抽出
            filtered_record = {k: v for k, v in record.items() if k in valid_columns}
            
            # raw_data_jsonに元データを保存
            obj_data = {
                **filtered_record,
                'raw_data_json': record.copy(),  # 元データをJSONで保存
            }
            orm_objects.append(model_class(**obj_data))
        
        try:
            # バルクインサート
            self.db.bulk_save_objects(orm_objects)
            self.db.commit()
            
            logger.info(f"Saved {len(orm_objects)} rows to {csv_type} table")
            return len(orm_objects)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save {csv_type} data: {e}")
            raise
    
    def _save_to_table(self, csv_type: str, df: pd.DataFrame, table_name: str) -> int:
        """
        カスタムテーブル名に保存（table_map 使用時）
        
        Args:
            csv_type: CSV種別（YAMLキー用）
            df: DataFrame
            table_name: 実際のテーブル名（例: "receive_flash"）
        
        Returns:
            int: 保存した行数
        """
        # カスタムテーブル用の動的モデル生成
        model_class = create_shogun_model_class(csv_type, table_name=table_name, schema=self._schema or "debug")
        
        # YAMLからカラム定義を取得
        columns_def = self.table_gen.get_columns_definition(csv_type)
        valid_columns = {col['en_name'] for col in columns_def}
        
        # DataFrameのカラムを検証
        df_columns = set(df.columns)
        missing_in_yaml = df_columns - valid_columns
        if missing_in_yaml:
            logger.warning(f"Columns in DataFrame but not in YAML for {csv_type}: {missing_in_yaml}")
        
        # DataFrameを辞書のリストに変換
        records = df.to_dict('records')
        
        # ORMオブジェクトのリストを作成
        orm_objects = []
        for record in records:
            # YAMLで定義されたカラムのみ抽出
            filtered_record = {k: v for k, v in record.items() if k in valid_columns}
            
            # raw_data_jsonに元データを保存
            obj_data = {
                **filtered_record,
                'raw_data_json': record.copy(),
            }
            orm_objects.append(model_class(**obj_data))
        
        try:
            # バルクインサート
            self.db.bulk_save_objects(orm_objects)
            self.db.commit()
            logger.info(f"Saved {len(orm_objects)} rows to custom table: {table_name}")
            return len(orm_objects)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save to custom table {table_name}: {e}")
            raise
    
    def save_receive_csv(self, df: pd.DataFrame) -> int:
        """受入一覧CSVを保存"""
        return self.save_csv_by_type('receive', df)
    
    def save_yard_csv(self, df: pd.DataFrame) -> int:
        """ヤード一覧CSVを保存"""
        return self.save_csv_by_type('yard', df)
    
    def save_shipment_csv(self, df: pd.DataFrame) -> int:
        """出荷一覧CSVを保存"""
        return self.save_csv_by_type('shipment', df)
    
    def truncate_table(self, csv_type: str) -> None:
        """
        指定したCSV種別のテーブルを全削除（開発・テスト用）
        
        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
        """
        table_name = self.settings.get_table_name(csv_type)
        if not table_name:
            raise ValueError(f"Unknown csv_type: {csv_type}")
        
        try:
            # TRUNCATE実行
            self.db.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
            self.db.commit()
            logger.info(f"Truncated table: {table_name}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to truncate {table_name}: {e}")
            raise
    
    def get_record_count(self, csv_type: str) -> int:
        """
        指定したCSV種別のテーブルのレコード数を取得
        
        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
            
        Returns:
            int: レコード数
        """
        model_class = get_shogun_model_class(csv_type)
        return self.db.query(model_class).count()
    
    def get_column_mapping(self, csv_type: str) -> Dict[str, str]:
        """
        YAMLから日本語→英語のカラムマッピングを取得
        
        Args:
            csv_type: CSV種別
            
        Returns:
            {'伝票日付': 'slip_date', ...}
        """
        return self.table_gen.get_column_mapping(csv_type)
