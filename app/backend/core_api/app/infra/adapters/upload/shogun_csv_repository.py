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
        schema = self._schema or "stg"
        # テーブル名は {csv_type}_shogun_flash (receive_shogun_flash, yard_shogun_flash, shipment_shogun_flash)
        table_name = f"{csv_type}_shogun_flash"
        model_class = create_shogun_model_class(csv_type, table_name=table_name, schema=schema)
        
        # YAMLから日本語→英語のカラムマッピングを取得
        column_mapping = self.table_gen.get_column_mapping(csv_type)
        
        # DataFrame のカラム名を日本語→英語に変換
        df = df.rename(columns=column_mapping)
        
        # YAMLからカラム定義を取得（英語カラム名）
        columns_def = self.table_gen.get_columns_definition(csv_type)
        valid_columns = [col['en_name'] for col in columns_def]
        
        # YAML で定義されたカラムのみを抽出（未定義カラムは WARNING ログで記録）
        df = filter_defined_columns(df, valid_columns, log_dropped=True)
        
        # SQL 保存可能な型に正規化（pandas特有の型をPython標準型に変換）
        df = to_sql_ready_df(df)
        
        # DataFrameを辞書のリストに変換してORMオブジェクトを作成
        records = df.to_dict('records')
        orm_objects = []
        for record in records:
            # Pandas特有の型をJSON互換型に変換（np.int64 → int, np.float64 → float等）
            payload = deep_jsonable(record)
            orm_objects.append(model_class(**payload))
        
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
        from app.infra.db.dynamic_models import create_shogun_model_class
        
        # スキーマ名を取得（指定がなければ "debug"）
        schema = self._schema or "debug"
        
        # CSV種別とスキーマに応じたSQLAlchemy ORMモデルクラスを動的生成
        model_class = create_shogun_model_class(csv_type, table_name=table_name, schema=schema)
        
        # 1. カラム名を英語に統一（日本語カラム名 → 英語カラム名）
        column_mapping = self.table_gen.get_column_mapping(csv_type)
        df = df.rename(columns=column_mapping)
        
        # 2. YAML定義に存在するカラムのみを抽出（未定義カラムは除外）
        columns_def = self.table_gen.get_columns_definition(csv_type)
        valid_columns = [col['en_name'] for col in columns_def]
        df = filter_defined_columns(df, valid_columns, log_dropped=True)
        
        # 3. SQL保存可能な型に正規化（pandas特有の型 → Python標準型）
        #    - pd.NaT / np.nan → None
        #    - np.int64 → int
        #    - np.float64 → float
        #    - pd.Timestamp → datetime.date / datetime.time
        df = to_sql_ready_df(df)
        
        # 4. 空行を除去（slip_dateがNULLの行はデータ不正として除外）
        if 'slip_date' in df.columns:
            original_len = len(df)
            df = df[df['slip_date'].notna()]
            if len(df) < original_len:
                logger.info(f"Empty rows removed: {original_len - len(df)} rows")
        
        # 5. DataFrameをORMオブジェクトのリストに変換
        records = df.to_dict('records')  # [{col1: val1, col2: val2, ...}, ...]
        orm_objects = []
        for record in records:
            # Pandas特有の型をJSON互換型に変換（np.int64 → int等）
            payload = deep_jsonable(record)
            # ORMモデルインスタンスを生成（**payloadで辞書をキーワード引数展開）
            orm_objects.append(model_class(**payload))
        
        try:
            # 6. データベースにコミット（add_all → commit）
            self.db.add_all(orm_objects)
            self.db.commit()
            logger.info(f"Successfully saved {len(orm_objects)} rows to {schema}.{table_name}")
            return len(orm_objects)
            
        except Exception as e:
            # エラー時はロールバックして例外を再送出
            self.db.rollback()
            logger.error(f"Failed to save to {schema}.{table_name}: {e}")
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

