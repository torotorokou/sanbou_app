"""
Shogun CSV Repository

将軍CSVデータをDBに保存するリポジトリ。
backend_sharedのCSVバリデーター・フォーマッターを活用します。
YAMLファイル(syogun_csv_masters.yaml)から動的にカラムマッピングを取得します。
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infra.db.dynamic_models import get_shogun_model_class, create_shogun_model_class
from app.config.settings import get_settings
from app.infra.db.table_definition import get_table_definition_generator
from app.shared.utils.df_normalizer import to_sql_ready_df, filter_defined_columns
from app.shared.utils.json_sanitizer import deep_jsonable

logger = logging.getLogger(__name__)


class ShogunCsvRepository:
    """将軍CSV保存リポジトリ（YAMLベース）"""
    
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
            df: 保存するDataFrame
                - raw層: 日本語カラム名（元のCSVそのまま）→ 英語に変換のみ、全カラム保持
                - stg層: 日本語カラム名（元のCSV）→ 英語に変換+YAML定義カラムのみ抽出
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {csv_type}, skipping save")
            return 0
        
        # スキーマとテーブル名の決定
        schema = self._schema or "stg"
        
        # テーブル名の上書きチェック
        override_table = self._table_map.get(csv_type)
        if override_table:
            # table_map が指定された場合: カスタムテーブル名を使用
            table_name = override_table
        else:
            # table_map が未指定の場合: デフォルトは *_shogun_flash
            # raw.receive_shogun_flash, stg.receive_shogun_flash など
            table_name = f"{csv_type}_shogun_flash"
        
        # YAMLから日本語→英語のカラムマッピングを取得
        column_mapping = self.table_gen.get_column_mapping(csv_type)
        
        # DataFrame のカラム名を日本語→英語に変換
        df_renamed = df.rename(columns=column_mapping)
        
        # raw層とstg層で異なる処理
        if schema == "raw":
            # raw層: 全カラムを保持（YAML定義外のカラムも含む）
            # TEXT型として保存（生データの完全性を保持）
            df_to_save = df_renamed.astype(str)  # 全カラムを文字列化
            df_to_save = df_to_save.replace(['nan', 'NaT', '<NA>'], '')  # pandas特有の文字列を空文字列に変換
            logger.debug(f"[raw] Saving {csv_type} with ALL columns ({len(df_to_save.columns)} cols): {list(df_to_save.columns)[:5]}...")
        else:
            # stg層: YAMLで定義されたカラムのみを抽出
            columns_def = self.table_gen.get_columns_definition(csv_type)
            valid_columns = [col['en_name'] for col in columns_def]
            df_to_save = filter_defined_columns(df_renamed, valid_columns, log_dropped=True)
            
            # SQL 保存可能な型に正規化（pandas特有の型をPython標準型に変換）
            df_to_save = to_sql_ready_df(df_to_save)
            logger.debug(f"[stg] Saving {csv_type} with YAML-defined columns ({len(df_to_save.columns)} cols): {list(df_to_save.columns)[:5]}...")
        
        model_class = create_shogun_model_class(csv_type, table_name=table_name, schema=schema)
        
        # DataFrameを辞書のリストに変換してORMオブジェクトを作成
        records = df_to_save.to_dict('records')
        orm_objects = []
        for record in records:
            # Pandas特有の型をJSON互換型に変換（np.int64 → int, np.float64 → float等）
            payload = deep_jsonable(record)
            orm_objects.append(model_class(**payload))
        
        try:
            # バルクインサート
            self.db.bulk_save_objects(orm_objects)
            self.db.commit()
            
            logger.info(f"Saved {len(orm_objects)} rows to {schema}.{table_name} (csv_type={csv_type})")
            return len(orm_objects)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save {csv_type} data to {schema}.{table_name}: {e}")
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

