"""
Raw Data Repository

CSV の生データ（変換前）を raw スキーマに保存するリポジトリ。
- raw.upload_file: ファイルメタ情報
- raw.receive_raw: 受入CSV の生データ（TEXT 型）

将来的に yard_raw, shipment_raw も追加可能。
"""

import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text, Table, MetaData, Column, Integer, BigInteger, Text, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)


class RawDataRepository:
    """生データ保存リポジトリ"""
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.metadata = MetaData()
        
        # upload_file テーブル定義
        self.upload_file_table = Table(
            'upload_file',
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('file_name', Text, nullable=False),
            Column('file_hash', String(64), nullable=False),
            Column('file_type', String(20), nullable=False),
            Column('csv_type', String(20), nullable=False),
            Column('file_size_bytes', BigInteger, nullable=True),
            Column('row_count', Integer, nullable=True),
            Column('uploaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
            Column('uploaded_by', String(100), nullable=True),
            Column('processing_status', String(20), server_default='pending'),
            Column('error_message', Text, nullable=True),
            Column('metadata', JSONB, nullable=True),
            schema='raw'
        )
        
        # receive_raw テーブル定義
        self.receive_raw_table = Table(
            'receive_raw',
            self.metadata,
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('file_id', Integer, ForeignKey('raw.upload_file.id'), nullable=False),
            Column('row_number', Integer, nullable=False),
            # 受入CSV の各カラム（TEXT 型、英語カラム名）
            Column('slip_date_text', Text, nullable=True),
            Column('sales_date_text', Text, nullable=True),
            Column('payment_date_text', Text, nullable=True),
            Column('vendor_cd_text', Text, nullable=True),
            Column('vendor_name_text', Text, nullable=True),
            Column('slip_type_cd_text', Text, nullable=True),
            Column('slip_type_name_text', Text, nullable=True),
            Column('item_cd_text', Text, nullable=True),
            Column('item_name_text', Text, nullable=True),
            Column('net_weight_text', Text, nullable=True),
            Column('quantity_text', Text, nullable=True),
            Column('unit_cd_text', Text, nullable=True),
            Column('unit_name_text', Text, nullable=True),
            Column('unit_price_text', Text, nullable=True),
            Column('amount_text', Text, nullable=True),
            Column('receive_no_text', Text, nullable=True),
            Column('aggregate_item_cd_text', Text, nullable=True),
            Column('aggregate_item_name_text', Text, nullable=True),
            Column('category_cd_text', Text, nullable=True),
            Column('category_name_text', Text, nullable=True),
            Column('weighing_time_gross_text', Text, nullable=True),
            Column('weighing_time_empty_text', Text, nullable=True),
            Column('site_cd_text', Text, nullable=True),
            Column('site_name_text', Text, nullable=True),
            Column('unload_vendor_cd_text', Text, nullable=True),
            Column('unload_vendor_name_text', Text, nullable=True),
            Column('unload_site_cd_text', Text, nullable=True),
            Column('unload_site_name_text', Text, nullable=True),
            Column('transport_vendor_cd_text', Text, nullable=True),
            Column('transport_vendor_name_text', Text, nullable=True),
            Column('client_cd_text', Text, nullable=True),
            Column('client_name_text', Text, nullable=True),
            Column('manifest_type_cd_text', Text, nullable=True),
            Column('manifest_type_name_text', Text, nullable=True),
            Column('manifest_no_text', Text, nullable=True),
            Column('sales_staff_cd_text', Text, nullable=True),
            Column('sales_staff_name_text', Text, nullable=True),
            Column('column38', Text, nullable=True),
            Column('column39', Text, nullable=True),
            Column('loaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
            schema='raw'
        )
        
        # yard_raw テーブル定義
        self.yard_raw_table = Table(
            'yard_raw',
            self.metadata,
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('file_id', Integer, ForeignKey('raw.upload_file.id'), nullable=False),
            Column('row_number', Integer, nullable=False),
            # ヤードCSV の各カラム（TEXT 型、英語カラム名）
            Column('slip_date_text', Text, nullable=True),
            Column('client_name_text', Text, nullable=True),
            Column('item_name_text', Text, nullable=True),
            Column('net_weight_text', Text, nullable=True),
            Column('quantity_text', Text, nullable=True),
            Column('unit_name_text', Text, nullable=True),
            Column('unit_price_text', Text, nullable=True),
            Column('amount_text', Text, nullable=True),
            Column('sales_staff_name_text', Text, nullable=True),
            Column('vendor_cd_text', Text, nullable=True),
            Column('vendor_name_text', Text, nullable=True),
            Column('category_cd_text', Text, nullable=True),
            Column('category_name_text', Text, nullable=True),
            Column('item_cd_text', Text, nullable=True),
            Column('slip_no_text', Text, nullable=True),
            Column('loaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
            schema='raw'
        )
        
        # shipment_raw テーブル定義
        self.shipment_raw_table = Table(
            'shipment_raw',
            self.metadata,
            Column('id', BigInteger, primary_key=True, autoincrement=True),
            Column('file_id', Integer, ForeignKey('raw.upload_file.id'), nullable=False),
            Column('row_number', Integer, nullable=False),
            # 出荷CSV の各カラム（TEXT 型、英語カラム名）
            Column('slip_date_text', Text, nullable=True),
            Column('shipment_no_text', Text, nullable=True),
            Column('client_name_text', Text, nullable=True),
            Column('vendor_cd_text', Text, nullable=True),
            Column('vendor_name_text', Text, nullable=True),
            Column('site_cd_text', Text, nullable=True),
            Column('site_name_text', Text, nullable=True),
            Column('item_name_text', Text, nullable=True),
            Column('net_weight_text', Text, nullable=True),
            Column('quantity_text', Text, nullable=True),
            Column('unit_name_text', Text, nullable=True),
            Column('unit_price_text', Text, nullable=True),
            Column('amount_text', Text, nullable=True),
            Column('transport_vendor_name_text', Text, nullable=True),
            Column('slip_type_name_text', Text, nullable=True),
            Column('detail_note_text', Text, nullable=True),
            Column('category_cd_text', Text, nullable=True),
            Column('category_name_text', Text, nullable=True),
            Column('loaded_at', DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
            schema='raw'
        )
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """
        ファイルの SHA-256 ハッシュを計算
        
        Args:
            file_content: ファイルの内容（バイト列）
            
        Returns:
            str: SHA-256 ハッシュ（16進数文字列）
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def create_upload_file(
        self,
        file_name: str,
        file_hash: str,
        file_type: str,
        csv_type: str,
        file_size_bytes: Optional[int] = None,
        row_count: Optional[int] = None,
        uploaded_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        アップロードファイルのメタ情報を登録
        
        Args:
            file_name: ファイル名
            file_hash: SHA-256 ハッシュ
            file_type: FLASH / FINAL
            csv_type: receive / yard / shipment
            file_size_bytes: ファイルサイズ
            row_count: データ行数
            uploaded_by: アップロードユーザー
            metadata: その他のメタ情報
            
        Returns:
            int: 登録された upload_file.id
        """
        try:
            result = self.db.execute(
                self.upload_file_table.insert().values(
                    file_name=file_name,
                    file_hash=file_hash,
                    file_type=file_type,
                    csv_type=csv_type,
                    file_size_bytes=file_size_bytes,
                    row_count=row_count,
                    uploaded_by=uploaded_by,
                    processing_status='pending',
                    metadata=metadata,
                ).returning(self.upload_file_table.c.id)
            )
            file_id = result.scalar_one()
            self.db.commit()
            logger.info(f"Created upload_file record: id={file_id}, hash={file_hash[:8]}...")
            return file_id
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create upload_file: {e}")
            raise
    
    def check_file_exists(self, file_hash: str, file_type: str, csv_type: str) -> Optional[int]:
        """
        同一ファイルがすでに登録されているかチェック
        
        Args:
            file_hash: SHA-256 ハッシュ
            file_type: FLASH / FINAL
            csv_type: receive / yard / shipment
            
        Returns:
            Optional[int]: 既存の upload_file.id、存在しない場合は None
        """
        result = self.db.execute(
            self.upload_file_table.select().where(
                self.upload_file_table.c.file_hash == file_hash,
                self.upload_file_table.c.file_type == file_type,
                self.upload_file_table.c.csv_type == csv_type,
            )
        ).fetchone()
        
        return result.id if result else None
    
    def update_upload_status(
        self,
        file_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """
        アップロードファイルの処理ステータスを更新
        
        Args:
            file_id: upload_file.id
            status: pending / processing / completed / failed
            error_message: エラーメッセージ
        """
        try:
            self.db.execute(
                self.upload_file_table.update()
                .where(self.upload_file_table.c.id == file_id)
                .values(
                    processing_status=status,
                    error_message=error_message,
                )
            )
            self.db.commit()
            logger.info(f"Updated upload_file {file_id} status to {status}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update upload_file status: {e}")
            raise
    
    def save_receive_raw(
        self,
        file_id: int,
        df: pd.DataFrame,
    ) -> int:
        """
        受入CSV の生データを raw.receive_raw に保存
        
        Args:
            file_id: upload_file.id
            df: 日本語カラム名のままの DataFrame（変換前）
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping raw save")
            return 0
        
        try:
            # 行番号を付与
            records = []
            for row_idx, (idx, row) in enumerate(df.iterrows(), start=1):
                record: Dict[str, Any] = {
                    'file_id': file_id,
                    'row_number': row_idx,  # 1-indexed
                }
                # DataFrame の各カラムを TEXT として保存
                for col in df.columns:
                    value = row[col]
                    # pd.NaT, np.nan, None はすべて None に正規化
                    if pd.isna(value):
                        record[col] = None
                    else:
                        # すべて文字列として保存
                        record[col] = str(value)
                
                records.append(record)
            
            # バルクインサート
            self.db.execute(self.receive_raw_table.insert(), records)
            self.db.commit()
            
            logger.info(f"Saved {len(records)} rows to raw.receive_raw (file_id={file_id})")
            return len(records)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save raw data: {e}")
            raise
    
    def save_yard_raw(
        self,
        file_id: int,
        df: pd.DataFrame,
    ) -> int:
        """
        ヤードCSV の生データを raw.yard_raw に保存
        
        Args:
            file_id: upload_file.id
            df: 日本語カラム名のままの DataFrame（変換前）
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping raw save")
            return 0
        
        try:
            # カラム名マッピング（日本語 → 英語）
            column_map = {
                '伝票日付': 'slip_date_text',
                '取引先名': 'client_name_text',
                '品名': 'item_name_text',
                '正味重量': 'net_weight_text',
                '数量': 'quantity_text',
                '単位名': 'unit_name_text',
                '単価': 'unit_price_text',
                '金額': 'amount_text',
                '営業担当者名': 'sales_staff_name_text',
                '業者CD': 'vendor_cd_text',
                '業者名': 'vendor_name_text',
                '種類CD': 'category_cd_text',
                '種類名': 'category_name_text',
                '品名CD': 'item_cd_text',
                '伝票番号': 'slip_no_text',
            }
            
            # 行番号を付与してレコード作成
            records = []
            for row_idx, (idx, row) in enumerate(df.iterrows(), start=1):
                record: Dict[str, Any] = {
                    'file_id': file_id,
                    'row_number': row_idx,
                }
                # DataFrame の各カラムを TEXT として保存（英語カラム名に変換）
                for jp_col, en_col in column_map.items():
                    if jp_col in df.columns:
                        value = row[jp_col]
                        record[en_col] = None if pd.isna(value) else str(value)
                
                records.append(record)
            
            # バルクインサート
            self.db.execute(self.yard_raw_table.insert(), records)
            self.db.commit()
            
            logger.info(f"Saved {len(records)} rows to raw.yard_raw (file_id={file_id})")
            return len(records)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save yard raw data: {e}")
            raise
    
    def save_shipment_raw(
        self,
        file_id: int,
        df: pd.DataFrame,
    ) -> int:
        """
        出荷CSV の生データを raw.shipment_raw に保存
        
        Args:
            file_id: upload_file.id
            df: 日本語カラム名のままの DataFrame（変換前）
            
        Returns:
            int: 保存した行数
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping raw save")
            return 0
        
        try:
            # カラム名マッピング（日本語 → 英語）
            column_map = {
                '伝票日付': 'slip_date_text',
                '出荷番号': 'shipment_no_text',
                '取引先名': 'client_name_text',
                '業者CD': 'vendor_cd_text',
                '業者名': 'vendor_name_text',
                '現場CD': 'site_cd_text',
                '現場名': 'site_name_text',
                '品名': 'item_name_text',
                '正味重量': 'net_weight_text',
                '数量': 'quantity_text',
                '単位名': 'unit_name_text',
                '単価': 'unit_price_text',
                '金額': 'amount_text',
                '運搬業者名': 'transport_vendor_name_text',
                '伝票区分名': 'slip_type_name_text',
                '明細備考': 'detail_note_text',
                '種類CD': 'category_cd_text',
                '種類名': 'category_name_text',
            }
            
            # 行番号を付与してレコード作成
            records = []
            for row_idx, (idx, row) in enumerate(df.iterrows(), start=1):
                record: Dict[str, Any] = {
                    'file_id': file_id,
                    'row_number': row_idx,
                }
                # DataFrame の各カラムを TEXT として保存（英語カラム名に変換）
                for jp_col, en_col in column_map.items():
                    if jp_col in df.columns:
                        value = row[jp_col]
                        record[en_col] = None if pd.isna(value) else str(value)
                
                records.append(record)
            
            # バルクインサート
            self.db.execute(self.shipment_raw_table.insert(), records)
            self.db.commit()
            
            logger.info(f"Saved {len(records)} rows to raw.shipment_raw (file_id={file_id})")
            return len(records)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save shipment raw data: {e}")
            raise
