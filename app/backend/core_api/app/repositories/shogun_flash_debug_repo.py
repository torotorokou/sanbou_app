"""
Shogun Flash Debug Repository

将軍速報版CSVを検証し、デバッグ用テーブル（debug スキーマ）に保存するリポジトリ。
起動時DDLで自動的にスキーマとテーブルを作成（Alembicは後回し）。
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import ValidationError

from app.domain.shogun_flash_schemas import (
    ReceiveFlashRow,
    ShipmentFlashRow,
    YardFlashRow,
)

logger = logging.getLogger(__name__)


class ShogunFlashDebugRepository:
    """将軍速報版デバッグ用リポジトリ"""
    
    # CSV種別とPydanticモデルのマッピング
    ROW_SCHEMAS = {
        'receive': ReceiveFlashRow,
        'shipment': ShipmentFlashRow,
        'yard': YardFlashRow,
    }
    
    # CSV種別とテーブル名のマッピング
    TABLE_NAMES = {
        'receive': 'debug.receive_flash',
        'shipment': 'debug.shipment_flash',
        'yard': 'debug.yard_flash',
    }
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_debug_schema()
        self._ensure_debug_tables()
    
    def _ensure_debug_schema(self) -> None:
        """debugスキーマを作成（存在しない場合）"""
        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS debug"))
            self.db.commit()
            logger.info("Debug schema ensured")
        except Exception as e:
            self.db.rollback()
            logger.warning(f"Failed to create debug schema (may already exist): {e}")
    
    def _ensure_debug_tables(self) -> None:
        """デバッグ用テーブルを作成（存在しない場合）"""
        
        # receive_flash テーブル
        receive_ddl = """
        CREATE TABLE IF NOT EXISTS debug.receive_flash (
            id SERIAL PRIMARY KEY,
            slip_date TIMESTAMP NOT NULL,
            sales_date TIMESTAMP,
            payment_date TIMESTAMP,
            vendor_cd INTEGER NOT NULL,
            vendor_name TEXT NOT NULL,
            slip_type_cd INTEGER,
            slip_type_name TEXT,
            item_cd INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            net_weight DOUBLE PRECISION NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            unit_cd INTEGER,
            unit_name TEXT,
            unit_price DOUBLE PRECISION,
            amount DOUBLE PRECISION,
            receive_no INTEGER NOT NULL,
            aggregate_item_cd INTEGER,
            aggregate_item_name TEXT,
            category_cd INTEGER,
            category_name TEXT,
            weighing_time_gross TEXT,
            weighing_time_empty TEXT,
            site_cd INTEGER,
            site_name TEXT,
            unload_vendor_cd INTEGER,
            unload_vendor_name TEXT,
            unload_site_cd INTEGER,
            unload_site_name TEXT,
            transport_vendor_cd INTEGER,
            transport_vendor_name TEXT,
            client_cd TEXT,
            client_name TEXT,
            manifest_type_cd INTEGER,
            manifest_type_name TEXT,
            manifest_no TEXT,
            sales_staff_cd INTEGER,
            sales_staff_name TEXT,
            raw_data_json JSONB,
            validation_errors JSONB,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # shipment_flash テーブル
        shipment_ddl = """
        CREATE TABLE IF NOT EXISTS debug.shipment_flash (
            id SERIAL PRIMARY KEY,
            slip_date TIMESTAMP NOT NULL,
            shipment_no TEXT NOT NULL,
            client_en_name TEXT NOT NULL,
            vendor_cd INTEGER NOT NULL,
            vendor_en_name TEXT NOT NULL,
            site_cd INTEGER,
            site_en_name TEXT,
            item_en_name TEXT NOT NULL,
            net_weight DOUBLE PRECISION NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            unit_en_name TEXT,
            unit_price DOUBLE PRECISION,
            amount DOUBLE PRECISION,
            transport_vendor_en_name TEXT,
            slip_type_en_name TEXT,
            detail_note TEXT,
            raw_data_json JSONB,
            validation_errors JSONB,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # yard_flash テーブル
        yard_ddl = """
        CREATE TABLE IF NOT EXISTS debug.yard_flash (
            id SERIAL PRIMARY KEY,
            slip_date TIMESTAMP NOT NULL,
            client_en_name TEXT NOT NULL,
            item_en_name TEXT NOT NULL,
            net_weight DOUBLE PRECISION NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            unit_en_name TEXT,
            unit_price DOUBLE PRECISION,
            amount DOUBLE PRECISION,
            sales_staff_en_name TEXT,
            vendor_cd INTEGER NOT NULL,
            vendor_en_name TEXT NOT NULL,
            category_cd INTEGER,
            category_en_name TEXT,
            item_cd INTEGER NOT NULL,
            slip_no TEXT,
            raw_data_json JSONB,
            validation_errors JSONB,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            self.db.execute(text(receive_ddl))
            self.db.execute(text(shipment_ddl))
            self.db.execute(text(yard_ddl))
            self.db.commit()
            logger.info("Debug tables ensured")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create debug tables: {e}")
            raise
    
    def validate_and_save(
        self,
        csv_type: str,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        DataFrameを行単位でPydantic検証し、デバッグテーブルに保存
        
        Args:
            csv_type: CSV種別 ('receive', 'shipment', 'yard')
            df: 検証対象のDataFrame（UTF-8, 英語カラム名想定）
            
        Returns:
            dict: 検証結果サマリー
            {
                'total_rows': int,
                'valid_rows': int,
                'invalid_rows': int,
                'saved_rows': int,
                'errors': List[dict]
            }
        """
        if csv_type not in self.ROW_SCHEMAS:
            raise ValueError(f"Unknown csv_type: {csv_type}")
        
        schema_class = self.ROW_SCHEMAS[csv_type]
        table_name = self.TABLE_NAMES[csv_type]
        
        total_rows = len(df)
        valid_rows = []
        invalid_rows = []
        errors = []
        
        # 行単位でバリデーション
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            # idx は pandas の Index型だが、実際には int
            row_num = int(idx) + 2 if isinstance(idx, (int, float)) else 2  # Excel風（ヘッダー=1行目）
            try:
                # Pydanticバリデーション
                validated = schema_class(**row_dict)
                valid_rows.append({
                    'data': validated.model_dump(),
                    'raw': row_dict,
                    'row_number': row_num,
                })
            except ValidationError as e:
                invalid_rows.append({
                    'row_number': row_num,
                    'errors': e.errors(),
                    'raw': row_dict,
                })
                errors.append({
                    'row': row_num,
                    'errors': [err['msg'] for err in e.errors()],
                })
                logger.warning(f"Validation error at row {row_num}: {e}")
        
        # デバッグテーブルに保存（valid/invalid両方を保存）
        saved_count = 0
        
        # 有効な行を保存
        for item in valid_rows:
            saved_count += self._insert_row(
                table_name=table_name,
                data=item['data'],
                raw_data=item['raw'],
                validation_errors=None,
            )
        
        # 無効な行も保存（デバッグ用）
        for item in invalid_rows:
            saved_count += self._insert_row(
                table_name=table_name,
                data=None,
                raw_data=item['raw'],
                validation_errors=item['errors'],
            )
        
        self.db.commit()
        
        result = {
            'total_rows': total_rows,
            'valid_rows': len(valid_rows),
            'invalid_rows': len(invalid_rows),
            'saved_rows': saved_count,
            'errors': errors,
        }
        
        logger.info(
            f"Validation complete for {csv_type}: "
            f"{len(valid_rows)}/{total_rows} valid, "
            f"{len(invalid_rows)} invalid"
        )
        
        return result
    
    def _insert_row(
        self,
        table_name: str,
        data: Dict[str, Any] | None,
        raw_data: Dict[str, Any],
        validation_errors: List[Dict[str, Any]] | None,
    ) -> int:
        """
        1行をデバッグテーブルに挿入
        
        Args:
            table_name: テーブル名
            data: 検証済みデータ（None=検証失敗）
            raw_data: 元データ（JSON）
            validation_errors: バリデーションエラー（あれば）
            
        Returns:
            int: 挿入行数（1 or 0）
        """
        try:
            if data is None:
                # 検証失敗行は validation_errors テーブルに保存（別テーブルがベスト）
                # ここでは簡略化のため、ログに記録して保存をスキップ
                logger.warning(
                    f"Skipping insert for invalid row into {table_name}. "
                    f"Errors: {validation_errors}"
                )
                return 0
            else:
                # 検証成功行は全カラムを保存
                columns = list(data.keys())
                placeholders = [f":{col}" for col in columns]
                columns_str = ', '.join(columns)
                placeholders_str = ', '.join(placeholders)
                
                insert_sql = f"""
                INSERT INTO {table_name} ({columns_str}, raw_data_json)
                VALUES ({placeholders_str}, :raw_data)
                """
                
                params = {**data, 'raw_data': json.dumps(raw_data, ensure_ascii=False, default=str)}
                self.db.execute(text(insert_sql), params)
            
            return 1
        except Exception as e:
            logger.error(f"Failed to insert row into {table_name}: {e}")
            return 0
    
    def truncate_table(self, csv_type: str) -> None:
        """デバッグテーブルをクリア"""
        if csv_type not in self.TABLE_NAMES:
            raise ValueError(f"Unknown csv_type: {csv_type}")
        
        table_name = self.TABLE_NAMES[csv_type]
        try:
            self.db.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY"))
            self.db.commit()
            logger.info(f"Truncated {table_name}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to truncate {table_name}: {e}")
            raise
